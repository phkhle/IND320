# IND320 – Energy Data Dashboard

## Project Overview

This project was developed for the IND320 course at the Norwegian University of Life Sciences (NMBU).

**Assignment 1:** Retrieves and visualizes Norwegian energy data from the NVE API.

**Assignment 2:** Extends the Streamlit dashboard with historical cross-border electricity import and export data from the ENTSO-E Transparency Platform.

**Assignment 3:** Weather and Time series analysis: Intergrates historical weather data from Open Meteo ERA5 and introduces anomaly detection, seasonal decomposition, and frequency analysis.

**Assignment 4:** Improves the dashboard design and navigation, introduces an interactive geographical map, integrates exchange rate data from Norges Bank, investigates time zone differences, and implements reservoir filling forecasting using River. It also introduces sliding window correlation analysis between weather and reservoir filling.

--

## Data Sources and Processing

### 1. NVE Reservoir Satistics
Reservoir statistics are retrieved from the Norwegian Water Resources and Energy Directorate (NVE) API.

The dashboard allows users to explore:

- Reservoir filling levels
- Storage capacity
- Weekly changes in reservoir filling
- Historical observations across geographical areas
- Seasonal patterns and long-term trends

NVE Atlas shapefiles are also used to define geographical boundaries. These boundaries are converted into GeoJSON for interactive map visualization.

### 2. ENTSO-E Electricity Data pipeline

The project uses Python, Apache Spark, Cassandra, and MongoDB Atlas to process and store electricity data.

```text
ENTSO-E API (2024–2025)
        |
        v
Historical CSV files
        |
        v
Apache Spark
        |
        v
Cassandra (394,464 observations)
        |
        v
Spark aggregation
    /          \
 Daily        Monthly
    \          /
     MongoDB Atlas
          |
          v
   Streamlit Dashboard
```

The dataset covers **nine electricity connections** involving Norway.

- **Cassandra:** Stores historical electricity observations in `ind320.entsoe_real`.
- **Apache Spark:** Validates and aggregates electricity data into daily and monthly totals.
- **MongoDB Atlas:** Stores aggregated data in `entsoe_daily` (6,579 documents) and `entsoe_monthly` (216 documents).
- **Streamlit:** Retrieves data from MongoDB Atlas and displays interactive visualizations.

### 3. Historical Weather Data - Open-Meteo ERA5
Assignment 3 introduces historical weather data using the Open-Meteo API and the ERA5 reanalysis model. The initial analysis focuses on NO3 during 2024.

The weather download functionality is implemented in ``weather_download.py``.

Weather observations are spatially aggregated across geographical regions and stored in Parquet files to avoid repeated API requests.

The main meteorological variables are:

- Temperature
- Precipitation

Weather data are used for:

- Interactive geographical visualization
- Statistical Process Control (SPC)
- Local Outlier Factor (LOF)
- Sliding window correlation analysis
- Reservoir filling forecasting

Assignment 4 additionally introduces historical daily weather data for NO3, aggregated to weekly resolution for forecasting.

### 4. Exchange Rate Data – Norges Bank

Assignment 4 introduces exchange rate data retrieved from the Norges Bank API.

The data retrieval functionality is implemented in `src/NB_API.py`.

The EUR/USD exchange rate is calculated using EUR/NOK and USD/NOK:

```text
EUR/USD = EUR/NOK / USD/NOK
```

The function and its usage are demonstrated in `assignment4.ipynb`.

### 5. Temporal Alignment and Time Zones

The project investigates differences in temporal representations across the data sources.

| Data source | Temporal representation |
|-------------|-------------------------|
| NVE | Weekly calendar dates |
| ENTSO-E | Timezone-aware timestamps |
| Open-Meteo ERA5 | UTC timestamps |
| Norges Bank | Daily calendar dates |

Timezone conversion, temporal aggregation, and date alignment are considered when combining observations from different sources.

Further details are provided in `assignment4.ipynb`.

---

## Streamlit Dashboard

The application is organized into four navigation groups: Home, Explore Data, Analysis, and Forecasting.


### Navigation Structure

```text
IND320 Energy Dashboard
│
├── Home
│   └── Dashboard Overview
│
├── Explore Data
│   ├── Reservoir Data Overview
│   ├── Reservoir Statistics
│   └── Electricity Transfers
│
├── Analysis
│   ├── STL & Spectrogram
│   ├── Weather Anomalies
│   └── Sliding Window Correlation
│
└── Forecasting
    └── Reservoir Filling Forecast
```

### Dashboard Pages

| Page | Description |
|------|-------------|
| Dashboard Overview | Interactive geographical map and navigation to other pages |
| Reservoir Data Overview | Summary of reservoir observations, filling levels, and storage capacity |
| Reservoir Statistics | Interactive visualization of historical reservoir statistics |
| Electricity Transfers | Annual and daily electricity imports and exports |
| STL & Spectrogram | Seasonal decomposition and frequency analysis |
| Weather Anomalies | Weather anomaly detection using SPC and LOF |
| Sliding Window Correlation | Rolling correlations between weather variables and reservoir filling |
| Reservoir Filling Forecast | Multi-step reservoir filling forecasting using River SNARIMAX |


## Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/phkhle/ind320.git
cd ind320
git switch project3
```

### 2. Create a Virtual Environment

On Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure MongoDB Atlas

Create a `.env` file in the project root:

```dotenv
MONGODB_URI=your_mongodb_connection_string
```

MongoDB Atlas access is required to display the ENTSO-E data.

### 5. Run Streamlit

```powershell
streamlit run streamlit_app.py
```

Rebuilding the historical data pipeline additionally requires ENTSO-E API access and a configured Spark/Cassandra environment.

## Limitations

- Reservoir filling forecasting is currently limited to NO3.
- Historical weather data availability varies across geographical regions and time periods.
- Water area boundaries are approximate geographical representations.
- Future weather inputs are estimated using historical averages rather than actual weather forecasts.
- Forecasting performance is based on validation experiments used for model selection.
- Experimental prediction intervals may contain physically unrealistic values and have not been calibrated or independently validated.
