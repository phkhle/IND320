import streamlit as st
import pandas as pd

# --------------------------------------------------
# Title
# --------------------------------------------------

st.title("Reservoir Data Plot")

st.write(
    "Explore monthly reservoir measurements by area type."
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
# Monthly averages by area type
# --------------------------------------------------

monthly_df = (
    df.groupby(["month", "omrType"])[measurement_columns]
    .mean()
    .reset_index()
)

monthly_df["month"] = monthly_df["month"].dt.to_timestamp()

# --------------------------------------------------
# Select area type
# --------------------------------------------------

selected_area = st.selectbox(
    "Select area type:",
    sorted(monthly_df["omrType"].unique())
)

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
    (monthly_df["omrType"] == selected_area)
    & (monthly_df["month"] >= start_month)
    & (monthly_df["month"] <= end_month)
].copy()

# --------------------------------------------------
# Interactive plot
# --------------------------------------------------

st.subheader(f"Reservoir measurements - {selected_area}")

if selected_column == "All columns":

    st.line_chart(
        plot_df,
        x="month",
        y=measurement_columns,
        x_label="Month",
        y_label="Value"
    )

else:

    st.line_chart(
        plot_df,
        x="month",
        y=selected_column,
        x_label="Month",
        y_label=selected_column
    )