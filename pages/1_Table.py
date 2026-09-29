import streamlit as st
import pandas as pd
from streamlit.column_config import LineChartColumn

# --------------------------------------------------
# 1_Data.py page
# --------------------------------------------------

st.title("Reservoir Data")


st.write(
    """
    This page displays the reservoir data imported from
    reservoirs.csv.
    """
)

# --------------------------------------------------
# Load data
# --------------------------------------------------

# decorator to cache the data loading function
@st.cache_data
def load_data():
    """
    Load the reservoir data from the local CSV file.

    Streamlit caches the result (st.cache_data) so that 
    the CSV does not need to be read from disk every time 
    the application reruns.

    """
    return pd.read_csv("reservoirs.csv")


df = load_data()


# --------------------------------------------------
# Display imported data
# --------------------------------------------------

st.header("Imported data")


st.dataframe(
    df,
    hide_index=True
)


# --------------------------------------------------
# Create row-wise data for LineChartColumn
# --------------------------------------------------

st.header("Overview of data series")


# These are the actual numerical reservoir measurements.
# The other numerical-looking columns are identifiers or
# time-related variables and should not be plotted.
measurement_columns = [
    "fyllingsgrad",
    "kapasitet_TWh",
    "fylling_TWh",
    "fyllingsgrad_forrige_uke",
    "endring_fyllingsgrad"
]

table_data = []

for column in df.columns:

    # Get the first observation in the column.
    first_value = df[column].iloc[0]

    # Only the numerical reservoir measurements should
    # be displayed as line-chart series.
    if column in measurement_columns:
        series = df[column].tolist()
    else:
        series = []

    table_data.append(
        {
            "Column": column,
            "First value": first_value,
            "Data series": series
        }
    )


# Convert the list to a DataFrame.
overview_df = pd.DataFrame(table_data)

# --------------------------------------------------
# Display row-wise table
# --------------------------------------------------

st.dataframe(
    overview_df,
    column_config={
        "Data series": LineChartColumn(
            "Data series"
        )
    },
    hide_index=True,
    use_container_width=True
)

