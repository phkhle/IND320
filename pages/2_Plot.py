
import streamlit as st
import pandas as pd

# Import function from NVE_API.py
from NVE_API import get_nve_data


# ============================================================
# 1. TITLE
# ============================================================

st.title("Reservoir Data Plot")

st.write(
    "Explore monthly reservoir measurements "
    "by area type and area number."
)


# ============================================================
# 2. LOAD DATA FROM NVE API
# ============================================================

@st.cache_data(ttl=3600)
def load_data():
    return get_nve_data()


df = load_data()

# Ensure date column is datetime
df["dato_Id"] = pd.to_datetime(df["dato_Id"])


# ============================================================
# 3. MEASUREMENT COLUMNS
# ============================================================

measurement_columns = [
    "fyllingsgrad",
    "kapasitet_TWh",
    "fylling_TWh",
    "fyllingsgrad_forrige_uke",
    "endring_fyllingsgrad"
]


# ============================================================
# 4. CREATE MONTH COLUMN
# ============================================================

df["month"] = df["dato_Id"].dt.to_period("M")


# ============================================================
# 5. SELECT AREA TYPE
# ============================================================

selected_area = st.radio(
    "Select area type:",
    options=["EL", "NO", "VASS"],
    horizontal=True
)


# ============================================================
# 6. SELECT MEASUREMENT
# ============================================================

selected_column = st.selectbox(
    "Select measurement:",
    ["All columns"] + measurement_columns
)


# ============================================================
# 7. SELECT MONTH RANGE
# ============================================================

months = sorted(df["month"].dropna().unique())

start_month, end_month = st.select_slider(
    "Select month range:",
    options=months,
    value=(months[0], months[-1]),
    format_func=lambda x: str(x)
)


# ============================================================
# 8. FILTER DATA
# ============================================================

filtered_df = df[
    (df["omrType"] == selected_area)
    & (df["month"] >= start_month)
    & (df["month"] <= end_month)
].copy()


# ============================================================
# 9. MONTHLY AVERAGES PER AREA NUMBER
# ============================================================

monthly_df = (
    filtered_df
    .groupby(["month", "omrnr"])[measurement_columns]
    .mean()
    .reset_index()
)

monthly_df["month"] = monthly_df["month"].dt.to_timestamp()


# ============================================================
# 10. FUNCTION TO CREATE PLOT DATA
# ============================================================

def create_plot_data(data, measurement):
    """
    Create a dataframe with:
    - One row per month
    - One column per area number
    """

    plot_df = data.pivot(
        index="month",
        columns="omrnr",
        values=measurement
    )

    plot_df = plot_df.sort_index()

    plot_df.columns = [
        f"Area {area_nr}"
        for area_nr in plot_df.columns
    ]

    return plot_df


# ============================================================
# 11. INTERACTIVE PLOTS
# ============================================================

if monthly_df.empty:

    st.warning("No data available for the selected period.")

elif selected_column == "All columns":

    # Plot each measurement separately
    for measurement in measurement_columns:

        st.subheader(f"{measurement} - {selected_area}")

        plot_df = create_plot_data(
            monthly_df,
            measurement
        )

        st.line_chart(
            plot_df,
            x_label="Month",
            y_label=measurement
        )

else:

    # Plot only the selected measurement
    st.subheader(f"{selected_column} - {selected_area}")

    plot_df = create_plot_data(
        monthly_df,
        selected_column
    )

    st.line_chart(
        plot_df,
        x_label="Month",
        y_label=selected_column
    )


# ============================================================
# 12. LINECHARTCOLUMN - MONTHLY TRENDS PER AREA
# ============================================================

st.subheader("Monthly trends per area")

# When All columns is selected, use filling level
# for the trend table.
trend_measurement = (
    "fyllingsgrad"
    if selected_column == "All columns"
    else selected_column
)

if not monthly_df.empty:

    trend_df = monthly_df.pivot(
        index="month",
        columns="omrnr",
        values=trend_measurement
    ).sort_index()

    # One row per area number
    trends_table = pd.DataFrame({
        "Area": [
            f"Area {area_nr}"
            for area_nr in trend_df.columns
        ],
        "Trend": [
            trend_df[area_nr].tolist()
            for area_nr in trend_df.columns
        ]
    })

    st.dataframe(
        trends_table,
        column_config={
            "Area": st.column_config.TextColumn(
                "Area number"
            ),
            "Trend": st.column_config.LineChartColumn(
                "Monthly trend",
                help=(
                    f"Monthly average of {trend_measurement} "
                    f"for the selected period"
                ),
                y_min=(
                    0
                    if trend_measurement == "fyllingsgrad"
                    else None
                )
            )
        },
        hide_index=True,
        use_container_width=True
    )


# ============================================================
# 13. DATA SOURCE
# ============================================================

with st.expander("Data source"):
    st.write(
        "Reservoir statistics are retrieved from "
        "the Norwegian Water Resources and Energy "
        "Directorate (NVE) API."
    )

    st.write(
        "The weekly observations are aggregated "
        "into monthly averages for each area number."
    )

    st.markdown(
        "[NVE Magasinstatistikk API]"
        "(https://biapi.nve.no/magasinstatistikk/swagger/index.html)"
    )
