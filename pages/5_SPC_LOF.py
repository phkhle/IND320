
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path

from analysis import (
    plot_precipitation_spc,
    plot_temperature_lof
)


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
def load_weather_data():

    project_root = Path(__file__).resolve().parent.parent

    file_path = (
        project_root
        / "data"
        / "weather"
        / "NO3_hourly_mean_2024.parquet"
    )

    df = pd.read_parquet(file_path)

    df["time"] = pd.to_datetime(df["time"])

    return df.sort_values("time").reset_index(drop=True)


weather_df = load_weather_data()


# ============================================================
# 3. SELECT REGION
# ============================================================

st.subheader("Weather Data Selection")

selected_el_area = st.session_state.get("selected_el_area", 3)

st.write("DEBUG - selected_el_area:", selected_el_area)
st.write(f"Selected electricity area: NO{selected_el_area}")

if selected_el_area != 3:
    st.warning(
        f"ERA5 weather data for NO{selected_el_area} "
        "is not available yet. Only NO3 has been downloaded."
    )
    st.stop()

st.caption(
    "ERA5 hourly reanalysis data for 2024, "
    "averaged across 1000 sampled locations."
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
        cutoff=cutoff,
        n_std=n_std
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
        contamination=contamination,
        n_neighbors=n_neighbors
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
        "1000 sampled locations in NO3."
    )
