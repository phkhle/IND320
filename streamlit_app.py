
import streamlit as st

from src.interactive_map import show_interactive_map
from src.forecast_controls import DEFAULT_CONFIG


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="IND320 Energy Dashboard",
    page_icon="⚡",
    layout="wide"
)

# ============================================================
# SHARED FORECAST CONFIGURATION
# ============================================================

if "use_default_forecast" not in st.session_state:

    st.session_state.use_default_forecast = True


if "training_start" not in st.session_state:

    st.session_state.training_start = (
        DEFAULT_CONFIG["training_start"]
    )


if "training_end" not in st.session_state:

    st.session_state.training_end = (
        DEFAULT_CONFIG["training_end"]
    )


if "forecast_exog_cols" not in st.session_state:

    st.session_state.forecast_exog_cols = (
        DEFAULT_CONFIG["exog_cols"].copy()
    )

if "forecast_horizon" not in st.session_state:

    st.session_state.forecast_horizon = (
        DEFAULT_CONFIG["horizon"]
    )
    
# ============================================================
# HOME PAGE
# ============================================================

def home_page():

    st.title("⚡ IND320 Energy Dashboard")

    st.write(
        "Explore Norwegian reservoir statistics, electricity "
        "transfers, weather patterns and reservoir filling forecasts."
    )

    # ========================================================
    # INTERACTIVE MAP
    # ========================================================

    show_interactive_map()

    st.divider()

    # ========================================================
    # DASHBOARD NAVIGATION
    # ========================================================

    st.header("Explore the Dashboard")

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:

        with st.container(border=True):

            st.subheader("📂 Explore Data")

            st.caption(
                "Explore historical energy and reservoir observations."
            )

            st.page_link(
                "pages/1_Reservoir_DataOverview.py",
                label="Reservoir Data Overview",
                icon="📋"
            )

            st.page_link(
                "pages/2_Reservoir_Statistics.py",
                label="Reservoir Statistics",
                icon="💧"
            )

            st.page_link(
                "pages/4_Power_Transfer.py",
                label="Electricity Transfers",
                icon="⚡"
            )

    with col2:

        with st.container(border=True):

            st.subheader("📊 Analysis")

            st.caption(
                "Investigate seasonal patterns and weather relationships."
            )

            st.page_link(
                "pages/3_Reservoir_TimeSeriesAnalysis.py",
                label="STL & Spectrogram",
                icon="📊"
            )

            st.page_link(
                "pages/5_Weather_Anomalies.py",
                label="Weather Anomalies",
                icon="🌦️"
            )

            st.page_link(
                "pages/6_Sliding_Correlation.py",
                label="Sliding Window Correlation",
                icon="📈"
            )

    with col3:

        with st.container(border=True):

            st.subheader("🔮 Forecasting")

            st.caption(
                "Predict future reservoir filling using SNARIMAX."
            )

            st.page_link(
                "pages/7_Forecasting.py",
                label="Reservoir Filling Forecast",
                icon="🔮"
            )

            st.caption("Currently available for NO3.")

    # ========================================================
    # ABOUT THE PROJECT
    # ========================================================

    st.divider()

    with st.expander("About the Project"):

        st.markdown("""
        This dashboard was developed as part of the IND320
        course at the Norwegian University of Life Sciences
        (NMBU), Autumn 2026.

        The project integrates energy and meteorological data
        with interactive visualization, time series analysis
        and machine learning.

        **Data sources**

        - NVE – Reservoir filling and storage statistics
        - ENTSO-E – Electricity imports and exports
        - Open-Meteo ERA5 – Historical weather observations
        - Norges Bank – Exchange rate data

        **Technologies**

        Python, Streamlit, Plotly, Folium, River,
        Apache Spark, Cassandra and MongoDB Atlas.
        """)

    st.caption("IND320 · NMBU · Autumn 2026")

# ============================================================
# NAVIGATION
# ============================================================

pages = {
    "Home": [
        st.Page(
            home_page,
            title="Dashboard Overview",
            icon="🏠",
            default=True
        )
    ],

    "Explore Data": [
        st.Page(
            "pages/1_Reservoir_DataOverview.py",
            title="Reservoir Data Overview",
            icon="📋"
        ),

        st.Page(
            "pages/2_Reservoir_Statistics.py",
            title="Reservoir Statistics",
            icon="💧"
        ),

        st.Page(
            "pages/4_Power_Transfer.py",
            title="Electricity Transfers",
            icon="⚡"
        )
    ],

    "Analysis": [
        st.Page(
            "pages/3_Reservoir_TimeSeriesAnalysis.py",
            title="STL & Spectrogram",
            icon="📊"
        ),

        st.Page(
            "pages/5_Weather_Anomalies.py",
            title="Weather Anomalies",
            icon="🌦️"
        ),
        
        st.Page(
            "pages/6_Sliding_Correlation.py",
            title="Sliding Window Correlation",
            icon="📈"
    )
    ],

    "Forecasting": [
        st.Page(
            "pages/7_Forecasting.py",
            title="Reservoir Filling Forecast",
            icon="🔮"
        )
    ]
}

navigation = st.navigation(pages)
navigation.run()

