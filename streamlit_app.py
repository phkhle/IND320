
import streamlit as st
from src.interactive_map import show_interactive_map

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="IND320 Energy Dashboard",
    page_icon="⚡",
    layout="wide"
)


# ============================================================
# HOME PAGE
# ============================================================

def home_page():

    st.title("⚡ IND320 Energy Dashboard")

    st.write(
        """
        An interactive dashboard for exploring Norwegian
        reservoir statistics, electricity transfers,
        weather anomalies, and forecasting.

        Developed as part of the IND320 course at NMBU.
        """
    )

    st.divider()

    st.header("Explore Norwegian Energy Regions")

    show_interactive_map()


    st.divider()

    st.header("About the Project")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("💧 Reservoir Statistics")
        st.write(
            "Explore historical reservoir filling levels, "
            "storage capacity, and weekly changes using NVE data."
        )

    with col2:
        st.subheader("⚡ Electricity Transfers")
        st.write(
            "Analyze electricity imports and exports using "
            "ENTSO-E data stored in MongoDB Atlas."
        )

    with col3:
        st.subheader("🌦️ Weather Analysis")
        st.write(
            "Explore ERA5 weather data and detect anomalies "
            "using SPC and Local Outlier Factor."
        )

    st.divider()

    st.header("Explore the Dashboard")

    st.write(
        "Use the sidebar to navigate between "
        "data exploration, analysis, and forecasting."
    )

    # Links to existing pages
    col1, col2 = st.columns(2)

    with col1:
        st.page_link(
            "pages/2_Reservoir_Statistics.py",
            label="💧 Reservoir Statistics"
        )

        st.page_link(
            "pages/4_Power_Transfer.py",
            label="⚡ Electricity Transfers"
        )

    with col2:
        st.page_link(
            "pages/3_Reservoir_TimeSeriesAnalysis.py",
            label="📊 Time Series Analysis"
        )

        st.page_link(
            "pages/5_Weather_Anomalies.py",
            label="🌦️ Weather Anomalies"
        )

    st.divider()

    st.caption(
        "Data sources: NVE API, ENTSO-E Transparency Platform, "
        "Open-Meteo ERA5 and Norges Bank | IND320 – NMBU, Autumn 2026"
    )


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
    ]
}

navigation = st.navigation(pages)
navigation.run()

