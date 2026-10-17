import streamlit as st
import pandas as pd

# --------------------------------------------------
# Title
# --------------------------------------------------

st.title("Reservoir Data Plot")

st.write(
    "This page shows the development of reservoir "
    "measurements over time for different area types."
)

# --------------------------------------------------
# Load data
# --------------------------------------------------

@st.cache_data
def load_data():
    return pd.read_csv("reservoirs.csv")


df = load_data()

df["dato_Id"] = pd.to_datetime(df["dato_Id"])

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
# Calculate monthly averages for each areaType
# --------------------------------------------------

monthly_df = (
    df.groupby(["month", "areaType"])[measurement_columns]
    .mean()
    .reset_index()
)

monthly_df["month"] = monthly_df["month"].dt.to_timestamp()

# --------------------------------------------------
# Select measurement
# --------------------------------------------------

selected_column = st.selectbox(
    "Select measurement:",
    ["All columns"] + measurement_columns
)

# --------------------------------------------------
# Select month range
# --------------------------------------------------

months = sorted(monthly_df["month"].unique())

start_month, end_month = st.select_slider(
    "Select month range:",
    options=months,
    value=(months[0], months[-1]),
    format_func=lambda x: pd.Timestamp(x).strftime("%Y-%m")
)

# --------------------------------------------------
# Filter data
# --------------------------------------------------

plot_df = monthly_df[
    (monthly_df["month"] >= start_month)
    & (monthly_df["month"] <= end_month)
].copy()

# --------------------------------------------------
# Interactive plot
# --------------------------------------------------

if selected_column == "All columns":

    # Convert wide data to long format
    long_df = plot_df.melt(
        id_vars=["month", "areaType"],
        value_vars=measurement_columns,
        var_name="measurement",
        value_name="value"
    )

    # Create separate series for each combination
    long_df["series"] = (
        long_df["areaType"].astype(str)
        + " - "
        + long_df["measurement"]
    )

    st.line_chart(
        long_df,
        x="month",
        y="value",
        color="series",
        x_label="Month",
        y_label="Value"
    )

else:

    st.line_chart(
        plot_df,
        x="month",
        y=selected_column,
        color="areaType",
        x_label="Month",
        y_label=selected_column
    )