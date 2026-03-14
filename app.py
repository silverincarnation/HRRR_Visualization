import streamlit as st
import duckdb
import geopandas as gpd
import h3
import pydeck as pdk
import pandas as pd
import os
import json
from shapely.geometry import Polygon

st.title("HRRR H3 Weather Map")

states = gpd.read_file(
    "https://eric.clst.org/assets/wiki/uploads/Stuff/gz_2010_us_040_00_500k.json")

states = states[(states.NAME != "Puerto Rico") & (states.NAME != "Alaska")]

schema = duckdb.sql("""
DESCRIBE SELECT * FROM 'output/*/*/*/*.parquet'
""").df()

columns = schema["column_name"].tolist()
columns.remove("h3")

st.sidebar.header("Filters")
var = st.sidebar.selectbox("Variable", columns)
states_selected = st.sidebar.multiselect(
    "States",
    sorted(states.NAME.tolist()),
    default=["Illinois"]
)

years = sorted(os.listdir("output"))
year = st.sidebar.selectbox("Year", years)

months = sorted(os.listdir(f"output/{year}"))
month = st.sidebar.selectbox("Month", months)

days = sorted(os.listdir(f"output/{year}/{month}"))
day = st.sidebar.selectbox("Day", days)

hour = st.sidebar.slider("Hour", 0, 23, 0)

path = f"output/{year}/{month}/{day}/{hour:02d}.parquet"

h3_cells = set()
for _, row in states[states.NAME.isin(states_selected)].iterrows():
    geom = row.geometry
    if geom.geom_type == "MultiPolygon":
        polys = geom.geoms
    else:
        polys = [geom]
    for poly in polys:
        polygon = {
            "type": "Polygon",
            "coordinates": [[(lon, lat) for lon, lat in poly.exterior.coords]]
        }
        h3_cells |= set(h3.geo_to_cells(polygon, res=5))

h3_cells = [str(x) for x in h3_cells]

if len(h3_cells) == 0:
    st.warning("No H3 cells found")
    st.stop()

query = f"""
SELECT *
FROM '{path}'
WHERE h3 IN ({",".join(["?"]*len(h3_cells))})
"""

df = duckdb.sql(query, params=h3_cells).df()

if len(df) == 0:
    st.warning("No data found")
    st.stop()

def h3_to_polygon(h):
    coords = h3.cell_to_boundary(h)
    return Polygon([(lng, lat) for lat, lng in coords])

df["geometry"] = df["h3"].apply(h3_to_polygon)

gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")

vmin = gdf[var].min()
vmax = gdf[var].max()

if vmax == vmin:
    gdf["color"] = 128
else:
    gdf["color"] = (
        (gdf[var] - vmin) / (vmax - vmin) * 255
    ).clip(0,255)

gdf_proj = gdf.to_crs(3857)
center = gdf_proj.geometry.centroid
center_lat = center.to_crs(4326).y.mean()
center_lon = center.to_crs(4326).x.mean()
geojson = json.loads(gdf.to_json())

h3_layer = pdk.Layer(
    "GeoJsonLayer",
    geojson,
    pickable=True,
    filled=True,
    stroked=False,
    get_fill_color="[properties.color, 80, 255-properties.color, 160]"
)

state_layer = pdk.Layer(
    "GeoJsonLayer",
    states[states.NAME.isin(states_selected)],
    filled=False,
    stroked=True,
    get_line_color=[255,255,255],
    get_line_width=200
)

deck = pdk.Deck(
    layers=[h3_layer, state_layer],
    initial_view_state=pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=5
    ),
    tooltip={
        "text": "{h3}\n" + "\n".join([f"{c}: {{{c}}}" for c in columns])
    }
)

st.pydeck_chart(deck)

with st.expander("Show Data"):
    st.dataframe(gdf.drop(columns="geometry").head(100))