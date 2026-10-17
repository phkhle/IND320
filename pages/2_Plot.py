import streamlit as st
import pandas as pd
# Import the get_nve_data function from NVE_API.py
from NVE_API import get_nve_data


# --------------------------------------------------
# Title
# --------------------------------------------------

st.title("Reservoir Data Plot")

st.write(
    "Explore monthly reservoir measurements "
    "by area type and area number."
)


# --------------------------------------------------
# Load data from NVE API
# --------------------------------------------------

@st.cache_data(ttl=3600)
def load_data():
    return get_nve_data()


df = load_data()


# --------------------------------------------------
# Measurement columns
# --------------------------------------------------

measurement_columns = [
    "fyllingsgrad",
    "kapasitet_TWh",
    "fylling_TWh",
    "fyllingsgrad_forrige_uke",
    "endring_fyllingsgrad"
]


# --------------------------------------------------
# Create month column
# --------------------------------------------------

df["month"] = df["dato_Id"].dt.to_period("M")


# --------------------------------------------------
# Select area type (EL, NO, VASS)
# --------------------------------------------------

selected_area = st.radio(
    "Select area type:",
    options=["EL", "NO", "VASS"],
    horizontal=True
)


# --------------------------------------------------
# Select measurement
# --------------------------------------------------

selected_column = st.selectbox(
    "Select measurement:",
    measurement_columns
)


# --------------------------------------------------
# Select month range
# --------------------------------------------------

months = sorted(df["month"].unique())

start_month, end_month = st.select_slider(
    "Select month range:",
    options=months,
    value=(months[0], months[-1]),
    format_func=lambda x: str(x)
)


# --------------------------------------------------
# Filter data
# --------------------------------------------------

filtered_df = df[
    (df["omrType"] == selected_area)
    & (df["month"] >= start_month)
    & (df["month"] <= end_month)
].copy()


# --------------------------------------------------
# Monthly average per area number
# --------------------------------------------------

monthly_df = (
    filtered_df
    .groupby(["month", "omrnr"])[selected_column]
    .mean()
    .reset_index()
)

monthly_df["month"] = monthly_df["month"].dt.to_timestamp()


# --------------------------------------------------
# Pivot: one column per area number
# --------------------------------------------------

plot_df = monthly_df.pivot(
    index="month",
    columns="omrnr",
    values=selected_column
)

plot_df.columns = [
    f"Area {area_nr}"
    for area_nr in plot_df.columns
]


# --------------------------------------------------
# Interactive plot
# --------------------------------------------------

st.subheader(
    f"{selected_column} - {selected_area}"
)

if plot_df.empty:
    st.warning("No data available for the selected period.")

else:
    st.line_chart(
        plot_df,
        x_label="Month",
        y_label=selected_column,
        color=None
    )




# --------------------------------------------------
# Data table with LineChartColumn
# --------------------------------------------------

st.subheader("Monthly trends per area")

if not plot_df.empty:

    # One row per area, one column per month
    trends_df = plot_df.T.copy()

    # Store monthly values as a list for each area
    trends_df["Trend"] = trends_df.apply(
        lambda row: row.tolist(),
        axis=1
    )

    trends_df = trends_df[["Trend"]]

    st.dataframe(
        trends_df,
        column_config={
            "Trend": st.column_config.LineChartColumn(
                "Monthly trend",
                help="Monthly average values for the selected period",
                y_min=0 if selected_column == "fyllingsgrad" else None,
            )
        },
        use_container_width=True
    )