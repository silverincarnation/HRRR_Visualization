# HRRR Visualization

## Data

This project uses meteorological data from the **HRRR (High-Resolution Rapid Refresh)** weather model [HRRR Official Website](https://rapidrefresh.noaa.gov/hrrr/) to build wind speed dashboard across the CONUS region.

## Dashboard

We developed an interactive **Streamlit dashboard** (`app.py`) to visualize the processed HRRR data.

The dashboard displays wind-related variables aggregated on an **H3 hexagonal grid with resolution = 5**, covering the **entire CONUS (Continental United States)**.

### Example

![Dashboard Example](dashboard.jpg)

## Environment 

Please refer to `requirements.txt`!
