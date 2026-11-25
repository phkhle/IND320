
import streamlit as st
import pandas as pd
from streamlit.column_config import LineChartColumn

from src.NVE_API import get_nve_data
from src.area_selector import (
    get_selected_area,
    set_selected_area
)

# ============================================================
# 1. PAGE HEADER
# ============================================================

st.title("Reservoir Data")

st.write(
    "Explore weekly Norwegian reservoir statistics "
    "retrieved directly from the NVE API."
)


# ============================================================
# 2. LOAD DATA
# ============================================================

@st.cache_data(ttl=3600)
def load_data():
    """Fetch and cache NVE reservoir data for one hour."""
    return get_nve_data()


try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to retrieve NVE data: {e}")
    st.stop()

if df.empty:
    st.warning("No reservoir data available.")
    st.stop()


# ============================================================
# 3. CLEAN DATA
# ============================================================

df["dato_Id"] = pd.to_datetime(
    df["dato_Id"], errors="coerce"
)

# Invalid dates such as 0001-01-01 become NaT.
df["neste_Publiseringsdato"] = pd.to_datetime(
    df["neste_Publiseringsdato"], errors="coerce"
)

measurement_columns = [
    "fyllingsgrad",
    "kapasitet_TWh",
    "fylling_TWh",
    "fyllingsgrad_forrige_uke",
    "endring_fyllingsgrad"
]

for column in measurement_columns:
    df[column] = pd.to_numeric(df[column], errors="coerce")

df = (
    df.dropna(subset=["dato_Id"])
    .sort_values("dato_Id")
    .reset_index(drop=True)
)

# ============================================================
# 4. FILTERS
# ============================================================

st.subheader("Select Data")

col1, col2 = st.columns([1, 2])

with col1:

    selected_type, selected_number = get_selected_area()

    st.session_state["_overview_area_type"] = selected_type

    def update_area_type():

        new_type = st.session_state["_overview_area_type"]

        current_type, current_number = get_selected_area()

        available_numbers = sorted(
            df.loc[
                df["omrType"] == new_type,
                "omrnr"
            ].dropna().unique().tolist()
        )

        if available_numbers:

            if current_number not in available_numbers:
                current_number = available_numbers[0]

            set_selected_area(new_type, current_number)

    area_type = st.radio(
        "Area type",
        options=["EL", "NO", "VASS"],
        horizontal=True,
        key="_overview_area_type",
        on_change=update_area_type,
        help=(
            "EL: Electricity price areas | "
            "NO: Norway | "
            "VASS: Watercourse areas"
        )
    )

# Filter area type
df_filtered = df[df["omrType"] == area_type].copy()

if df_filtered.empty:
    st.info("No observations for the selected area type.")
    st.stop()


# ============================================================
# 5. FILTER BY PERIOD
# ============================================================

first_date = df_filtered["dato_Id"].min().date()
last_date = df_filtered["dato_Id"].max().date()

with col2:
    start_date, end_date = st.slider(
        "Select time period",
        min_value=first_date,
        max_value=last_date,
        value=(first_date, last_date),
        format="YYYY-MM-DD"
    )

# Filter selected date range
df_filtered = df_filtered[
    (df_filtered["dato_Id"].dt.date >= start_date)
    & (df_filtered["dato_Id"].dt.date <= end_date)
].copy()

if df_filtered.empty:
    st.warning("No observations for the selected period.")
    st.stop()

# ============================================================
# 6. OVERVIEW TABLE WITH MINI CHARTS
# ============================================================

st.subheader("Reservoir Overview")

st.caption(
    f"{len(df_filtered):,} observations | "
    f"{df_filtered['dato_Id'].min():%Y-%m-%d} to "
    f"{df_filtered['dato_Id'].max():%Y-%m-%d}"
)

overview_rows = []

for area_number, group in df_filtered.groupby("omrnr"):

    group = group.sort_values("dato_Id")

    # One row per area, with the latest values.
    latest = group.iloc[-1]

    # Preserve missing values in the trend.
    filling_trend = group["fyllingsgrad"].tolist()
    capacity_trend = group["kapasitet_TWh"].tolist()

    if area_type == "EL":
        area_name = f"NO {area_number}"
    elif area_type == "NO":
        area_name = "Norway"
    else:
        area_name = f"Watercourse {area_number}"

    overview_rows.append({
        "Area": area_name,
        "Observations": len(group),
        "Latest date": latest["dato_Id"],
        "Filling level": latest["fyllingsgrad"] * 100,
        "Weekly change": latest["endring_fyllingsgrad"] * 100,
        "Filling trend": filling_trend,
        "Capacity trend": capacity_trend
    })


overview_df = pd.DataFrame(overview_rows)

st.dataframe(
    overview_df,
    column_config={
        "Latest date": st.column_config.DateColumn(
            "Latest date",
            format="YYYY-MM-DD"
        ),
        "Filling level": st.column_config.NumberColumn(
            "Filling level",
            format="%.1f%%"
        ),
        "Weekly change": st.column_config.NumberColumn(
            "Weekly change",
            format="%+.2f pp"
        ),
        "Filling trend": LineChartColumn(
            "Filling trend",
            y_min=0,
            y_max=1
        ),
        "Capacity trend": LineChartColumn(
            "Capacity (TWh)"
        )
    },
    hide_index=True,
    use_container_width=True
)


# ============================================================
# 7. DETAILED OBSERVATIONS
# ============================================================

with st.expander("View detailed observations"):

    st.write(
        "Weekly reservoir measurements for the selected "
        "area type and time period."
    )

    display_columns = [
        "dato_Id",
        "omrType",
        "omrnr",
        "iso_aar",
        "iso_uke",
        "fyllingsgrad",
        "kapasitet_TWh",
        "fylling_TWh",
        "fyllingsgrad_forrige_uke",
        "endring_fyllingsgrad"
    ]

    st.dataframe(
        df_filtered[display_columns].sort_values(
            ["dato_Id", "omrnr"],
            ascending=[False, True]
        ),
        hide_index=True,
        use_container_width=True
    )

    st.download_button(
        "Download filtered data (CSV)",
        data=df_filtered[display_columns].to_csv(
            index=False
        ).encode("utf-8"),
        file_name="nve_reservoir_data.csv",
        mime="text/csv"
    )


# ============================================================
# 8. DATA SOURCE
# ============================================================

st.caption(
    "Source: Norwegian Water Resources and Energy "
    "Directorate (NVE) – Magasinstatistikk API."
)
