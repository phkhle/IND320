
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

from analysis import (
    plot_precipitation_spc,
    plot_temperature_lof
)

from NVE_API import get_nve_data
from area_selector import select_area
from weather_download import download_and_save_region_weather

import weather_download


# ============================================================
# 1. PAGE TITLE
# ============================================================

st.title("Weather Anomaly Detection")

st.write(
    "Detect precipitation and temperature anomalies "
    "using Statistical Process Control and Local Outlier Factor."
)


# ============================================================
# 2. LOAD WEATHER DATA
# ============================================================

@st.cache_data
def load_weather_data(region):

    project_root = Path(__file__).resolve().parent.parent

    file_path = (
        project_root
        / "data"
        / "weather"
        / f"{region}_hourly_mean_2024.parquet"
    )

    df = pd.read_parquet(file_path)
    # Standardize weather column names
    df = df.rename(columns={
        "precipitation": "precipitation_mean",
        "temperature_2m": "temperature_mean"
    })

    df["time"] = pd.to_datetime(df["time"], utc=True)


    return df.sort_values("time").reset_index(drop=True)


# ============================================================
# 3. SHARED AREA SELECTION
# ============================================================

st.subheader("Weather Data Selection")


# Load NVE data for the shared area selector
@st.cache_data(ttl=3600)
def load_nve_data():
    return get_nve_data()


df_nve = load_nve_data()

# Use the same selector as the reservoir pages
selected_area, selected_number = select_area(df_nve)



# ============================================================
# 4. CHECK WEATHER DATA AVAILABILITY
# ============================================================


project_root = Path(__file__).resolve().parent.parent


def get_weather_region(area_type, area_number):
    """Map the selected reservoir area to a weather region."""

    if area_type == "EL" and area_number in (1, 2, 3, 4, 5):
        return f"NO{area_number}"

    if area_type == "VASS":
        return {
            1: "Øst",
            2: "Vest",
            3: "Nord"
        }.get(area_number)

    return None

region = get_weather_region(selected_area, selected_number)

# This part was inspeired by another student's work
if region is None:
    st.info(
        "Weather data are available for electricity areas "
        "(NO1–NO5) and precipitation areas (VASS1–VASS3)."
    )
    st.stop()

weather_file = (
    project_root
    / "data"
    / "weather"
    / f"{region}_hourly_mean_2024.parquet"
)

if weather_file.exists():

    st.success(f"ERA5 weather data available for {region}.")

else:

    st.warning(
        f"ERA5 weather data for {region} "
        "has not been downloaded yet."
    )

    if st.button("Download ERA5 weather data"):

        with st.spinner(
            f"Downloading ERA5 weather data for {region}..."
        ):

            try:
                output_path = download_and_save_region_weather(
                    region=region,
                    start_date="2024-01-01",
                    end_date="2024-12-31",
                    n_locations=1000,
                )

                st.success("Weather download completed.")

                st.rerun()

            except Exception as e:
                st.error(f"Download failed: {e}")

    st.stop()

weather_df = load_weather_data(region)




st.caption(
    f"ERA5 hourly reanalysis data for 2024, "
    f"averaged across 1000 locations in {region}."
)



# ============================================================
# 4. CREATE ANALYSIS TABS
# ============================================================

tab1, tab2 = st.tabs([
    "Precipitation – SPC",
    "Temperature – LOF"
])


# ============================================================
# 5. SPC ANALYSIS
# ============================================================

with tab1:

    st.subheader("Precipitation Anomaly Detection")

    st.write(
        "Apply DCT high-pass filtering and robust "
        "Statistical Process Control to identify "
        "unusual precipitation observations."
    )

    col1, col2 = st.columns(2)

    with col1:

        cutoff = st.slider(
            "DCT cutoff",
            min_value=1,
            max_value=200,
            value=30
        )

    with col2:

        n_std = st.slider(
            "Number of standard deviations",
            min_value=1.0,
            max_value=5.0,
            value=3.0,
            step=0.5
        )

    fig, summary = plot_precipitation_spc(
        df=weather_df,
        region = region,
        cutoff=cutoff,
        n_std=n_std,
  
    )

    st.pyplot(fig)
    plt.close(fig)

    with st.expander("SPC Summary"):
        st.write(summary)


# ============================================================
# 6. LOF ANALYSIS
# ============================================================

with tab2:

    st.subheader("Temperature Anomaly Detection")

    st.write(
        "Use Local Outlier Factor to identify "
        "unusual hourly temperatures."
    )

    col1, col2 = st.columns(2)

    with col1:

        contamination = st.slider(
            "Expected proportion of outliers (%)",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1
        ) / 100

    with col2:

        n_neighbors = st.slider(
            "Number of neighbors",
            min_value=5,
            max_value=100,
            value=20
        )

    fig, summary = plot_temperature_lof(
        df=weather_df,
        region = region,
        contamination=contamination,
        n_neighbors=n_neighbors,
        
    )

    st.pyplot(fig)
    plt.close(fig)

    with st.expander("LOF Summary"):
        st.write(summary)


# ============================================================
# 7. DATA SOURCE
# ============================================================

st.divider()

with st.expander("Data source"):

    st.write(
        "Weather data is retrieved from Open-Meteo "
        "using the ERA5 historical reanalysis model."
    )

    st.write(
        "The hourly precipitation and temperature "
        "values represent spatial averages across "
        f"1000 sampled locations in {region}."
    )

