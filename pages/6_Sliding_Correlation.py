import streamlit as st
import pandas as pd

from pathlib import Path

from src.analysis import plot_sliding_correlation
from src.NVE_API import get_nve_data
from src.area_selector import select_area


st.title("Sliding Window Correlation")

st.write(
    "Explore the relationship between weather "
    "and reservoir filling degree using rolling correlation."
)


# ============================================================
# 1. LOAD DATA
# ============================================================

@st.cache_data(ttl=3600)
def load_nve_data():
    return get_nve_data()


@st.cache_data
def load_weather_data(region):

    project_root = Path(__file__).resolve().parent.parent

    file_path = (
        project_root
        / "data"
        / "weather"
        / f"{region}_hourly_mean_2024.parquet"
    )

    df = pd.read_parquet(file_path)

    df = df.rename(columns={
        "temperature_2m": "temperature_mean",
        "precipitation": "precipitation_mean"
    })

    df["time"] = pd.to_datetime(df["time"], utc=True)

    return df


df_nve = load_nve_data()

selected_area, selected_number = select_area(df_nve)


# ============================================================
# 2. SELECT WEATHER REGION
# ============================================================

def get_weather_region(area_type, area_number):

    if area_type == "EL" and area_number in (1, 2, 3, 4, 5):
        return f"NO{area_number}"

    if area_type == "VASS":
        return {
            1: "Øst",
            2: "Vest",
            3: "Nord"
        }.get(area_number)

    return None


region = get_weather_region(selected_area, selected_number)

if region is None:
    st.info("Select an electricity or reservoir area.")
    st.stop()


# ============================================================
# 3. FILTER NVE DATA
# ============================================================

nve = df_nve[
    (df_nve["omrType"] == selected_area) &
    (df_nve["omrnr"] == selected_number)
].copy()

nve["date"] = pd.to_datetime(nve["dato_Id"])

nve = nve[["date", "fyllingsgrad"]]


# ============================================================
# 4. AGGREGATE WEATHER TO WEEKLY DATA
# ============================================================

project_root = Path(__file__).resolve().parent.parent

weather_path = (
    project_root
    / "data"
    / "weather"
    / f"{region}_hourly_mean_2024.parquet"
)

if not weather_path.exists():
    st.warning(f"Weather data for {region} are unavailable.")
    st.stop()

weather = load_weather_data(region)

# Convert UTC timestamps to date-based weekly periods
weather["time"] = (
    weather["time"]
    .dt.tz_convert(None)
)

weather = weather.set_index("time")

# NVE dates represent weekly observations on Sundays
weekly_weather = weather.resample("W-SUN").agg(
    temperature_mean=("temperature_mean", "mean"),
    precipitation_mean=("precipitation_mean", "sum"),
    n_temperature=("temperature_mean", "count"),
    n_precipitation=("precipitation_mean", "count")
).reset_index()

# Keep only complete weeks (7 * 24 hours)
weekly_weather = weekly_weather.loc[
    (weekly_weather["n_temperature"] == 168) &
    (weekly_weather["n_precipitation"] == 168)
].drop(columns=["n_temperature", "n_precipitation"])

weekly_weather = weekly_weather.rename(columns={"time": "date"})


# ============================================================
# 5. MERGE DATA
# ============================================================

df = pd.merge(
    nve,
    weekly_weather,
    on="date",
    how="inner"
).sort_values("date")

if df.empty:
    st.warning("No overlapping NVE and weather observations.")
    st.stop()


# ============================================================
# 6. INTERACTIVE CONTROLS
# ============================================================

st.subheader(f"Correlation Analysis – {region}")

weather_property = st.selectbox(
    "Weather property",
    ["Temperature", "Precipitation"],
    index=0
)

col1, col2 = st.columns(2)

with col1:
    window = st.slider(
        "Window length (weeks)",
        min_value=4,
        max_value=26,
        value=12
    )

with col2:
    lag = st.slider(
        "Weather lag (weeks)",
        min_value=0,
        max_value=12,
        value=0
    )


# ============================================================
# 7. PLOT CORRELATION
# ============================================================

fig, result = plot_sliding_correlation(
    df=df,
    weather_property=weather_property,
    window=window,
    lag=lag
)

fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)"
)

st.plotly_chart(
    fig,
    use_container_width=True,
    theme="streamlit"
)
st.caption(
    f"Using {len(df)} weekly observations. "
    "Positive lag means earlier weather is compared "
    "with later reservoir filling."
)

st.write(
    "Mean rolling correlation:",
    round(result["correlation"].mean(), 3)
)