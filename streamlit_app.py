
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
    statistics and cross-border electricity flows.

    Developed as part of the IND320 course at the
    Norwegian University of Life Sciences (NMBU).
    """
)

st.divider()

# ============================================================
# PROJECT OVERVIEW
# ============================================================

st.header("About the Project")

col1, col2 = st.columns(2)

with col1:
    st.subheader("💧 Reservoir Data – NVE")

    st.write(
        """
        Explore Norwegian reservoir statistics retrieved
        from the NVE API.

        The dashboard provides historical reservoir filling
        levels, storage capacity, and weekly changes.
        """
    )

with col2:
    st.subheader("⚡ Electricity Transfers – ENTSO-E")

    st.write(
        """
        Analyze electricity imports and exports between
        Norway and neighboring electricity market areas.

        Historical data from 2024–2025 is processed using
        Apache Spark and Cassandra, then stored in
        MongoDB Atlas for visualization.
        """
    )

st.divider()

# ============================================================
# NAVIGATION
# ============================================================

st.header("Explore the Dashboard")

st.write("Use the sidebar to navigate between the pages.")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.subheader("Table")
        st.write(
            "Browse NVE reservoir measurements, "
            "filter by area and period, and explore trends."
        )
        st.page_link(
            "pages/1_Table.py",
            label="Open Table",
            icon="📋"
        )

with col2:
    with st.container(border=True):
        st.subheader("Plot")
        st.write(
            "Explore historical reservoir data "
            "through interactive visualizations."
        )
        st.page_link(
            "pages/2_Plot.py",
            label="Open Plot",
            icon="📈"
        )

with col3:
    with st.container(border=True):
        st.subheader("Transfer")
        st.write(
            "Compare electricity imports and exports "
            "and analyze daily transfer trends."
        )
        st.page_link(
            "pages/3_Transfer.py",
            label="Open Transfer",
            icon="⚡"
        )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Data sources: NVE API and ENTSO-E Transparency Platform | "
    "IND320 – NMBU, Autumn 2026"
)
