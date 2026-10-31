# IND320 – Energy Data Dashboard

## Project Overview

This project was developed for the IND320 course at the Norwegian University of Life Sciences (NMBU).

**Assignment 1:** Retrieves and visualizes Norwegian energy data from the NVE API.

**Assignment 2:** Extends the Streamlit dashboard with historical cross-border electricity import and export data from the ENTSO-E Transparency Platform.

## Data Pipeline

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

## Streamlit Dashboard

The dashboard includes three pages:

| Page | Description |
|------|-------------|
| Table | Displays NVE energy data |
| Plot | Visualizes NVE data |
| Transfer | Visualizes ENTSO-E electricity imports and exports |

The **Transfer** page allows users to:

- Select an electricity connection and year.
- Compare annual imports and exports using a pie chart.
- Explore daily electricity flows for selected months using an interactive line chart.

## Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/phkhle/ind320.git
cd ind320
git switch project2
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
