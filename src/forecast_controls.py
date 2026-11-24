import streamlit as st
import pandas as pd

from pathlib import Path
from src.NVE_API import get_nve_data


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG = {
    "region": "NO3",
    "training_start": pd.Timestamp("2021-11-28").date(),
    "training_end": pd.Timestamp("2026-11-15").date(),
    "horizon": 12,
    "exog_cols": ["temperature_mean"],
    "p": 1,
    "d": 1,
    "q": 2,
    "m": 52,
    "sp": 2,
    "sd": 0,
    "sq": 0
}

# ============================================================
# 1. LOAD RESERVOIR DATA
# ============================================================

@st.cache_data(ttl=3600)
def load_reservoir_data(region):

    df = get_nve_data()

    region_number = int(region.replace("NO", ""))

    df = df.loc[
        (df["omrType"] == "EL") &
        (df["omrnr"] == region_number)
    ].copy()

    df["dato_Id"] = (
        pd.to_datetime(df["dato_Id"])
        .dt.tz_localize(None)
        .dt.normalize()
    )

    return df.sort_values("dato_Id").reset_index(drop=True)


# ============================================================
# 2. LOAD WEEKLY WEATHER DATA
# ============================================================

@st.cache_data
def load_weekly_weather(region):

    folder = (
        PROJECT_ROOT / "data" / "weather_daily" / region
    )

    files = sorted(
        folder.glob(
            f"{region}_2019-01-01_2026-11-15_*.parquet"
        )
    )

    if not files:
        raise ValueError(
            f"No weather data available for {region}."
        )

    df = pd.concat(
        [pd.read_parquet(file) for file in files],
        ignore_index=True
    )

    df["time"] = pd.to_datetime(df["time"])

    daily = (
        df.groupby("time")
        .agg(
            temperature_mean=("temperature_2m_mean", "mean"),
            precipitation_mean=("precipitation_sum", "mean")
        )
    )

    weekly = (
        daily.resample("W-SUN")
        .agg(
            temperature_mean=("temperature_mean", "mean"),
            precipitation_sum=("precipitation_mean", "sum"),
            n_days=("temperature_mean", "count")
        )
        .reset_index()
        .rename(columns={"time": "dato_Id"})
    )

    weekly = weekly.loc[weekly["n_days"] == 7]

    return weekly[
        ["dato_Id", "temperature_mean", "precipitation_sum"]
    ]


# ============================================================
# 3. GET AVAILABLE DATA
# ============================================================

def get_available_data(region="NO3", exog_cols=None):

    df = load_reservoir_data(region)

    exog_cols = list(exog_cols or [])

    if exog_cols:

        weather = load_weekly_weather(region)

        df = df.merge(
            weather,
            on="dato_Id",
            how="inner",
            validate="one_to_one"
        )

    df = df.dropna(
        subset=["dato_Id", "fyllingsgrad"] + exog_cols
    )

    if df.empty:
        raise ValueError(
            "No data available for the selected configuration."
        )

    return df.sort_values("dato_Id").reset_index(drop=True)


# ============================================================
# 4. SHARED TRAINING DATE SELECTORS
# ============================================================

def show_training_period(df, prefix, disabled=False):


    min_date = df["dato_Id"].min().date()
    max_date = df["dato_Id"].max().date()

    # Default: last 260 weekly observations
    default_start = max(
        min_date,
        (
            pd.Timestamp(max_date)
            - pd.Timedelta(weeks=259)
        ).date()
    )

    if "training_start" not in st.session_state:
        st.session_state.training_start = default_start

    if "training_end" not in st.session_state:
        st.session_state.training_end = max_date

    # Keep shared dates within available data
    start = min(
        max(st.session_state.training_start, min_date),
        max_date
    )

    end = min(
        max(st.session_state.training_end, start),
        max_date
    )

    start_key = f"{prefix}_training_start"
    end_key = f"{prefix}_training_end"

    st.session_state[start_key] = start
    st.session_state[end_key] = end

    # Save changes to shared session state
    def update_start():

        st.session_state.training_start = (
            st.session_state[start_key]
        )

        if (
            st.session_state.training_end
            < st.session_state.training_start
        ):
            st.session_state.training_end = (
                st.session_state.training_start
            )

        # Switch to custom configuration
        st.session_state.use_default_forecast = False


    def update_end():

        st.session_state.training_end = (
        st.session_state[end_key]
    )

        # Switch to custom configuration
        st.session_state.use_default_forecast = False

    st.caption(
        f"Available data: {min_date} – {max_date}"
    )

    training_start = st.date_input(
        "Training start",
        min_value=min_date,
        max_value=max_date,
        key=start_key,
        on_change=update_start,
        disabled=disabled
    )

    training_end = st.date_input(
        "Training end",
        min_value=training_start,
        max_value=max_date,
        key=end_key,
        on_change=update_end,
        disabled=disabled
    )

    st.session_state.training_start = training_start
    st.session_state.training_end = training_end

    return training_start, training_end


# ============================================================
# 5. SHARED FORECAST HORIZON
# ============================================================

def show_forecast_horizon(prefix, disabled=False):

    # Initialize shared forecast horizon
    if "forecast_horizon" not in st.session_state:

        st.session_state.forecast_horizon = (
            DEFAULT_CONFIG["horizon"]
        )

    # Use recommended horizon when default mode is enabled
    if disabled:

        st.session_state.forecast_horizon = (
            DEFAULT_CONFIG["horizon"]
        )

    # Separate widget key for each page
    horizon_key = f"{prefix}_horizon_widget"

    st.session_state[horizon_key] = (
        st.session_state.forecast_horizon
    )

    # Synchronize changes across pages
    def update_horizon():

        st.session_state.forecast_horizon = (
            st.session_state[horizon_key]
        )

    horizon = st.slider(
        "Forecast horizon (weeks)",
        min_value=1,
        max_value=26,
        key=horizon_key,
        on_change=update_horizon,
        disabled=disabled
    )

    return horizon