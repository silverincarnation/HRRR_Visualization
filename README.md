# GSRCONUS

## Project Overview

We are currently in the model development stage of the GSR CONUS project. To model wind speed across the CONUS region, we used 24 meteorological variables derived from HRRR and built three initial modeling approaches. Our work focused on constructing a wind-speed modeling pipeline, organizing HRRR features within the H3 hexagonal grid system, and visualizing spatial wind patterns by linking H3 cells with wind-related attributes.

## Data

This project uses meteorological data from the **HRRR (High-Resolution Rapid Refresh)** weather model [HRRR Official Website](https://rapidrefresh.noaa.gov/hrrr/) to build wind speed modeling pipelines across the CONUS region.

### Variables

We extracted **24 meteorological variables** representing both surface conditions and atmospheric features at multiple pressure levels.

#### Surface variables

- `UGRD:10 m above ground` — zonal wind component  (used in training as both an input feature (t) and a prediction target (t+1))
- `VGRD:10 m above ground` — meridional wind component  (used in training as both an input feature (t) and a prediction target (t+1))
- `TMP:2 m above ground` — surface temperature  
- `MSLMA:mean sea level` — mean sea level pressure  

#### Pressure-level variables

The following variables were collected at **50 mb, 500 mb, 850 mb, and 1000 mb**:

- `HGT` — geopotential height  
- `SPFH` — specific humidity  
- `TMP` — temperature  
- `UGRD` — zonal wind component  
- `VGRD` — meridional wind component  

Together, these variables capture atmospheric structure, thermodynamic conditions, and wind dynamics relevant to wind speed modeling.

### Train-Test Split

We used HRRR data from **January 1 2025 to January 4 2025** as the **training set**, and data from **January 5 2025** as the **test set**.

### Data Processing

- Raw HRRR data were retrieved and organized by timestamp.
- Meteorological variables were spatially aggregated (max) using the H3 hexagonal grid system.
- Processed datasets were stored in **Parquet format** for efficient storage and fast downstream loading.

### Storage Format

Each processed file is saved as a **Parquet** file and contains:

- `h3_index`
- meteorological input features
- wind-related target variables

This data structure supports efficient model training, evaluation, and geospatial visualization.

## Model 1: Xgboost

The XGBoost model was configured with the following hyperparameters:

- `n_estimators = 500`
- `max_depth = 8`
- `learning_rate = 0.05`
- `subsample = 0.8`
- `colsample_bytree = 0.8`
- `tree_method = "hist"`
- `n_jobs = -1`
- `random_state = 42`

### Forecast Performance Over Time

![RMSE over time](pictures/model1.jpg)

This degradation suggests that the current model only captures short-term wind dynamics 

## Model 2: Xgboost with nearby features

Model 2 extends Model 1 by incorporating spatial context from neighboring H3 cells.
Instead of using only local meteorological variables, this model augments the feature set with statistics computed from nearby grid cells.

For each H3 cell, the model aggregates features from its immediate neighbors (H3 ring = 1) and computes:
- mean of neighbor features
- standard deviation of neighbor features

These aggregated statistics are concatenated with the original local features, allowing the model to capture spatial correlations in the atmospheric field.

As a result, the input feature vector becomes:
```
[self features, neighbor mean, neighbor std]
```

### Model Configuration

The XGBoost model was configured with the following hyperparameters:

- `n_estimators = 300`
- `max_depth = 8`
- `learning_rate = 0.05`
- `subsample = 0.8`
- `colsample_bytree = 0.8`
- `tree_method = "hist"`
- `n_jobs = -1`
- `random_state = 42`

Two independent models were trained:
- one to predict `u10`
- one to predict `v10`

### Model Performance over time

![RMSE over time](pictures/model2.png)

## Model 3: GNN

### Overview
This model introduces a Graph Neural Network (GNN) to capture spatial relationships between weather observations across the H3 grid. Unlike the baseline models, which treat each location independently, the GNN explicitly models interactions between neighboring cells in the spatial grid.

Weather systems exhibit strong spatial dependencies: conditions at a given location are influenced by nearby regions. By representing the H3 grid as a graph, the model can learn these relationships and improve short-term wind prediction.

The model predicts next-hour 10m wind components (u10, v10) using atmospheric variables from the HRRR dataset.

### Graph Representation
The HRRR data is mapped onto an **H3 hexagonal grid**, where:
* **Nodes** represent H3 cells (spatial locations)
* **Edges** connect neighboring hex cells
* **Node** features contain atmospheric variables from HRRR
  
Each node includes multiple weather features such as:
* wind components (`u10`, `v10`)
* temperature (`t2m`)
* mean sea level pressure (`mslma`)
* temperature, wind, humidity, and geopotential height at multiple pressure levels
  
This produces a graph with:
* **N nodes (H3 cells)**
* **E edges connecting spatial neighbors**
* **F atmospheric features per node**

### Model Architecture
The model uses **GraphSAGE**, a widely used GNN architecture for learning on large graphs.

Architecture:
```markdown
Node Features
      │
GraphSAGE Layer
      │
ReLU
      │
GraphSAGE Layer
      │
ReLU
      │
Linear Layer
      │
Predicted Wind Components (u10, v10)
```

Key characteristics:
* Two **GraphSAGE convolution layers** capture spatial information from neighboring cells.
* A **linear layer** produces predictions for wind components.
* The model is trained using **Mean Squared Error (MSE)** loss.

### Results
The Graph Neural Network model was trained to predict next-hour wind components (`u10`, `v10`) across the H3 spatial grid.

Example training output:
```markdown
Epoch 01 | Train Loss: 1.6384 | Val Loss: 1.2422 | RMSE u10: 1.1036 | RMSE v10: 1.1253
Epoch 20 | Train Loss: 0.9018 | Val Loss: 0.8811 | RMSE u10: 0.9090 | RMSE v10: 0.9674
Epoch 30 | Train Loss: 0.8779 | Val Loss: 0.8811 | RMSE u10: 0.9060 | RMSE v10: 0.9702
```

## Dashboard

We developed an interactive **Streamlit dashboard** (`app.py`) to visualize the processed HRRR data.

The dashboard displays wind-related variables aggregated on an **H3 hexagonal grid with resolution = 5**, covering the **entire CONUS (Continental United States)**.

### Example

![Dashboard Example](pictures/dashboard.jpg)

## Environment & Credentials

To access the S3 buckets, you must configure your AWS credentials via a `.env` file in the project root.

Create a file named `.env` with:

```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
