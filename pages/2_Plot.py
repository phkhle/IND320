import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------------
# 2_Plot.py
# --------------------------------------------------

st.title("Reservoir Data Plot")

st.write(
    """
    This page shows the development of the reservoir
    measurements over time.
    """
)


# --------------------------------------------------
# Load data
# --------------------------------------------------

@st.cache_data
def load_data():
    """
    Load the reservoir data from the local CSV file.

    Streamlit caches the result so the CSV does not need
    to be read from disk every time the application reruns.
    """
    return pd.read_csv("reservoirs.csv")


df = load_data()


# --------------------------------------------------
# Convert date column
# --------------------------------------------------

df["dato_Id"] = pd.to_datetime(df["dato_Id"])


# --------------------------------------------------
# Define the numerical measurement columns
# --------------------------------------------------

measurement_columns = [
    "fyllingsgrad",
    "kapasitet_TWh",
    "fylling_TWh",
    "fyllingsgrad_forrige_uke",
    "endring_fyllingsgrad"
]


# --------------------------------------------------
# Create a month column
# --------------------------------------------------

df["month"] = df["dato_Id"].dt.to_period("M")


# --------------------------------------------------
# Calculate monthly averages
# --------------------------------------------------

monthly_df = (
    df.groupby("month")[measurement_columns]
    .mean()
    .reset_index()
)


# --------------------------------------------------
# Convert Period to timestamp
# --------------------------------------------------

monthly_df["month"] = monthly_df["month"].dt.to_timestamp()


# --------------------------------------------------
# Select data series
# --------------------------------------------------

column_options = ["All columns"] + measurement_columns

selected_column = st.selectbox(
    "Select data to plot:",
    column_options
)


# --------------------------------------------------
# Select month
# --------------------------------------------------

months = monthly_df["month"].tolist()

selected_month = st.select_slider(
    "Select the last month to display:",
    options=months,
    value=months[0],
    format_func=lambda x: x.strftime("%Y-%m")
)


# --------------------------------------------------
# Select the subset of months
# --------------------------------------------------

plot_df = monthly_df[
    monthly_df["month"] <= selected_month
].copy()


# --------------------------------------------------
# Create the plot
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(12, 6))


if selected_column == "All columns":

    for column in measurement_columns:

        ax.plot(
            plot_df["month"],
            plot_df[column],
            label=column
        )

else:

    ax.plot(
        plot_df["month"],
        plot_df[selected_column],
        label=selected_column
    )


# --------------------------------------------------
# Format the plot
# --------------------------------------------------

ax.set_title("Monthly Reservoir Measurements")

ax.set_xlabel("Month")

ax.set_ylabel("Value")

ax.grid(True)

ax.legend()

plt.xticks(rotation=45)

plt.tight_layout()


# --------------------------------------------------
# Display the plot
# --------------------------------------------------

st.pyplot(fig)