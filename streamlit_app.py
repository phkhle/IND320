
import streamlit as st

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="IND320 Energy Dashboard",
    page_icon="⚡",
    layout="wide"
)

# ============================================================
# HEADER
# ============================================================

st.title("⚡ IND320 Energy Dashboard")

st.write(
    """
    An interactive dashboard for exploring Norwegian reservoir
    statistics, electricity transfers, and weather anomalies.

    Developed as part of the IND320 course at the
    Norwegian University of Life Sciences (NMBU).
    """
)

st.divider()

# ============================================================
# PROJECT OVERVIEW
# ============================================================

st.header("About the Project")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("💧 Reservoir Statistics")
    st.write(
        """
        Explore historical reservoir filling levels,
        storage capacity, and weekly changes using
        data from the NVE API.
        """
    )

with col2:
    st.subheader("⚡ Electricity Transfers")
    st.write(
        """
        Analyze electricity imports and exports
        using ENTSO-E data processed with Apache Spark
        and stored in MongoDB Atlas.
        """
    )

with col3:
    st.subheader("🌦️ Weather Analysis")
    st.write(
        """
        Explore ERA5 temperature and precipitation
        data and detect anomalies using Statistical
        Process Control and Local Outlier Factor.
        """
    )

st.divider()

# ============================================================
# NAVIGATION
# ============================================================

st.header("Explore the Dashboard")

st.write("Use the sidebar or the links below to navigate between pages.")

# ------------------------------------------------------------
# 1. RESERVOIR DATA OVERVIEW
# ------------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.subheader("1. Reservoir Data Overview")
        st.write(
            "Browse NVE reservoir measurements and "
            "filter data by area and period."
        )
        st.page_link(
            "pages/1_Reservoir_DataOverview.py",
            label="Open Data Overview",
            icon="📋"
        )

# ------------------------------------------------------------
# 2. RESERVOIR STATISTICS
# ------------------------------------------------------------

with col2:
    with st.container(border=True):
        st.subheader("2. Reservoir Statistics")
        st.write(
            "Explore monthly reservoir measurements "
            "and historical trends."
        )
        st.page_link(
            "pages/2_Reservoir_Statistics.py",
            label="Open Reservoir Statistics",
            icon="📈"
        )

# ------------------------------------------------------------
# 3. TIME SERIES ANALYSIS
# ------------------------------------------------------------

with col3:
    with st.container(border=True):
        st.subheader("3. Reservoir Time Series Analysis")
        st.write(
            "Analyze reservoir filling levels using "
            "STL decomposition and spectrograms."
        )
        st.page_link(
            "pages/3_Reservoir_TimeSeriesAnalysis.py",
            label="Open Time Series Analysis",
            icon="📊"
        )

# ------------------------------------------------------------
# 4. ELECTRICITY TRANSFERS
# ------------------------------------------------------------

col4, col5 = st.columns(2)

with col4:
    with st.container(border=True):
        st.subheader("4. Electricity Transfers")
        st.write(
            "Compare electricity imports and exports "
            "and analyze daily transfer trends."
        )
        st.page_link(
            "pages/4_Power_Transfer.py",
            label="Open Electricity Transfers",
            icon="⚡"
        )

# ------------------------------------------------------------
# 5. WEATHER ANOMALY DETECTION
# ------------------------------------------------------------

with col5:
    with st.container(border=True):
        st.subheader("5. Weather Anomaly Detection")
        st.write(
            "Detect precipitation and temperature anomalies "
            "using DCT-based SPC and Local Outlier Factor."
        )
        st.page_link(
            "pages/5_Weather_Anomalies.py",
            label="Open Weather Anomalies",
            icon="🌦️"
        )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Data sources: NVE API, ENTSO-E Transparency Platform "
    "and Open-Meteo ERA5 | IND320 – NMBU, Autumn 2026"
)
