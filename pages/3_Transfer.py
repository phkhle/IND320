
import streamlit as st
import pandas as pd
import plotly.express as px

from MongoDB_API import get_entsoe_monthly_data


# ============================================================
# 1. PAGE TITLE
# ============================================================

st.title("Electricity Transfers – Norway")

st.write(
    "Explore real electricity imports and exports between Norway "
    "and neighboring countries using ENTSO-E data from 2024–2025."
)


# ============================================================
# 2. FETCH REAL DATA FROM MONGODB
# ============================================================

@st.cache_data(ttl=3600)
def load_data():
    """
    Load real monthly ENTSO-E electricity transfer data
    from MongoDB Atlas.
    """
    return get_entsoe_monthly_data()


df = load_data()

if df.empty:
    st.warning("No data available in MongoDB.")
    st.stop()


# Convert month to datetime and extract year
df["month"] = pd.to_datetime(df["month"], format="%Y-%m")
df["year"] = df["month"].dt.year

# Ensure numeric columns
df["total_import_mwh"] = pd.to_numeric(
    df["total_import_mwh"], errors="coerce"
)

df["total_export_mwh"] = pd.to_numeric(
    df["total_export_mwh"], errors="coerce"
)


# ============================================================
# 3. SELECT CONNECTION AND YEAR
# ============================================================

connection = st.selectbox(
    "Select connection",
    options=sorted(df["connection"].unique())
)

# Available years for selected connection
connection_df = df[df["connection"] == connection]

available_years = sorted(
    connection_df["year"].unique(),
    reverse=True
)

selected_year = st.radio(
    "Select year",
    options=available_years,
    horizontal=True
)

# Filter data
df_filtered = df[
    (df["connection"] == connection) &
    (df["year"] == selected_year)
].copy()

df_filtered = df_filtered.sort_values("month")


# ============================================================
# 4. CALCULATE TOTAL IMPORT AND EXPORT
# ============================================================

total_import = df_filtered["total_import_mwh"].sum()
total_export = df_filtered["total_export_mwh"].sum()

net_import = total_import - total_export


# Display summary metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Import (MWh)",
        f"{total_import:,.0f}"
    )

with col2:
    st.metric(
        "Total Export (MWh)",
        f"{total_export:,.0f}"
    )

with col3:
    st.metric(
        "Net Import (MWh)",
        f"{net_import:,.0f}"
    )


# ============================================================
# 5. PIE CHART - IMPORT VS EXPORT
# ============================================================

st.subheader(f"Import vs Export – {connection} ({selected_year})")

pie_df = pd.DataFrame({
    "Direction": ["Import", "Export"],
    "MWh": [total_import, total_export]
})

if pie_df["MWh"].sum() > 0:

    fig_pie = px.pie(
        pie_df,
        names="Direction",
        values="MWh",
        title=f"Electricity Transfers – {connection} ({selected_year})",
        hole=0.3
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )

else:
    st.info("No electricity transfers available for this period.")


# ============================================================
# 6. MONTHLY ELECTRICITY TRANSFERS
# ============================================================

st.subheader("Monthly Import and Export")

# Create readable month labels
df_filtered["month_label"] = df_filtered["month"].dt.strftime("%Y-%m")

available_months = df_filtered["month_label"].tolist()

selected_months = st.multiselect(
    "Select months",
    options=available_months,
    default=available_months
)

monthly_filtered = df_filtered[
    df_filtered["month_label"].isin(selected_months)
].copy()


if not monthly_filtered.empty:

    monthly_filtered = monthly_filtered.sort_values("month")

    # Convert wide data to long format for Plotly
    plot_df = monthly_filtered.melt(
        id_vars=["month", "month_label"],
        value_vars=[
            "total_import_mwh",
            "total_export_mwh"
        ],
        var_name="Direction",
        value_name="MWh"
    )

    plot_df["Direction"] = plot_df["Direction"].replace({
        "total_import_mwh": "Import",
        "total_export_mwh": "Export"
    })

    fig_line = px.line(
        plot_df,
        x="month",
        y="MWh",
        color="Direction",
        markers=True,
        title=f"Monthly Electricity Transfers – {connection} ({selected_year})",
        labels={
            "month": "Month",
            "MWh": "Electricity (MWh)"
        }
    )

    fig_line.update_layout(
        xaxis=dict(
            tickformat="%b %Y"
        ),
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_line,
        use_container_width=True
    )

else:
    st.info("Please select at least one month.")


# ============================================================
# 7. DATA SOURCE AND RAW DATA
# ============================================================

with st.expander("Data source and monthly observations"):

    st.write("**Source:** ENTSO-E Transparency Platform")
    st.write("**Database:** MongoDB Atlas – IND320.entsoe_monthly")
    st.write("**Data type:** Real electricity transfer observations")
    st.write("**Period:** January 2024 – December 2025")
    st.write("**Unit:** MWh")

    display_df = df_filtered[
        [
            "connection",
            "month_label",
            "total_import_mwh",
            "total_export_mwh"
        ]
    ].copy()

    display_df = display_df.rename(columns={
        "month_label": "Month",
        "total_import_mwh": "Import (MWh)",
        "total_export_mwh": "Export (MWh)"
    })

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
