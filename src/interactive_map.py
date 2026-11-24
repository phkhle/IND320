
import json
from pathlib import Path

import folium
import streamlit as st
import pandas as pd
import branca.colormap as cm

from streamlit_folium import st_folium

from src.forecast_controls import (
    get_available_data,
    show_training_period,
    show_forecast_horizon
)

# ============================================================
# 1. FILE PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PRICE_GEOJSON_PATH = (
    PROJECT_ROOT / "data" / "price_areas.geojson"
)

WEATHER_GEOJSON_PATH = (
    PROJECT_ROOT / "data" / "weather_regions.geojson"
)

WEATHER_DATA_DIR = PROJECT_ROOT / "data" / "weather"


# ============================================================
# 2. LOAD GEOGRAPHICAL DATA
# ============================================================

@st.cache_data
def load_price_areas():
    """Load electricity price area polygons (NO1-NO5)."""

    with open(PRICE_GEOJSON_PATH, encoding="utf-8") as file:
        return json.load(file)


@st.cache_data
def load_weather_regions():
    """Load weather region polygons (Øst, Vest, Nord)."""

    with open(WEATHER_GEOJSON_PATH, encoding="utf-8") as file:
        return json.load(file)


# ============================================================
# 3. LOAD WEATHER DATA
# ============================================================

@st.cache_data
def read_weather_files(file_paths):
    """Read available aggregated hourly weather files."""

    datasets = []

    for file_path in file_paths:
        path = Path(file_path)

        # Expected filename: REGION_hourly_mean_2024.parquet
        region = path.name.split("_hourly_mean_")[0]

        df = pd.read_parquet(path)

        df["region"] = region
        df["time"] = pd.to_datetime(df["time"], utc=True)

        datasets.append(df)

    if not datasets:
        return pd.DataFrame()

    return pd.concat(datasets, ignore_index=True)


def load_weather_data():
    """Discover and load available aggregated weather files."""

    file_paths = tuple(
        str(path)
        for path in sorted(
            WEATHER_DATA_DIR.glob("*_hourly_mean_*.parquet")
        )
    )

    return read_weather_files(file_paths)


# ============================================================
# 4. AGGREGATE WEATHER DATA
# ============================================================

def aggregate_weather(df, start_date, end_date, property_name):
    """
    Aggregate hourly weather observations for a selected period.

    Temperature: mean over the period.
    Precipitation: sum of hourly spatial means.
    """

    if df.empty:
        return {}

    start = pd.Timestamp(start_date).tz_localize("UTC")

    end = (
        pd.Timestamp(end_date).tz_localize("UTC")
        + pd.Timedelta(days=1)
    )

    filtered = df.loc[
        (df["time"] >= start) &
        (df["time"] < end)
    ]

    if filtered.empty:
        return {}

    if property_name == "Temperature":
        result = filtered.groupby("region")["temperature_mean"].mean()

    else:
        result = filtered.groupby("region")["precipitation_mean"].sum()

    return result.to_dict()


# ============================================================
# 5. INTERACTIVE MAP
# ============================================================

def show_interactive_map():
    """
    Display an interactive geographical map with:

    - Electricity price areas (NO1-NO5)
    - Weather regions (Øst, Vest, Nord)
    - Temperature and precipitation colouring
    - Shared region selection
    """

    # --------------------------------------------------------
    # 5.1 Initialize session state
    # --------------------------------------------------------

    if "map_layer" not in st.session_state:
        st.session_state.map_layer = "Price Area"

    if "selected_region" not in st.session_state:
        st.session_state.selected_region = "NO1"

    # --------------------------------------------------------
    # 5.2 Layout
    # --------------------------------------------------------

    col_map, col_selector = st.columns([3, 1])

    # --------------------------------------------------------
    # 5.3 Controls
    # --------------------------------------------------------

    with col_selector:

        st.subheader("Area Selection")

        map_layer = st.selectbox(
            "Select map layer",
            [
                "Price Area",
                "Water Area",
                "Weather Property"
            ],
            key="map_layer"
        )

        # ----------------------------------------------------
        # Shared forecasting period
        # ----------------------------------------------------

        st.subheader("Forecast Training Period")
        use_default = st.session_state.get(
        "use_default_forecast",
        True
)

        if use_default:

            st.caption(
                "Using the recommended model configuration. "
                "To customize the settings, disable the recommended "
                "configuration on the Forecasting page."
            )

        else:

            st.caption(
                "Training period and forecast horizon are "
                "synchronized with the Forecasting page."
            )

        try:

            df_forecast_available = get_available_data(
                region="NO3",
                exog_cols=st.session_state.get(
                    "forecast_exog_cols",
                    ["temperature_mean"]
                )
            )

            training_start, training_end = show_training_period(
                df=df_forecast_available,
                prefix="map",
                disabled=use_default
            )

            horizon = show_forecast_horizon(
                prefix="map",
                disabled=use_default
            )

            # Find the last available weekly training observation
            last_observation = df_forecast_available.loc[
                (
                    df_forecast_available["dato_Id"]
                    >= pd.Timestamp(training_start)
                ) &
                (
                    df_forecast_available["dato_Id"]
                    <= pd.Timestamp(training_end)
                ),
                "dato_Id"
            ].max()

            if pd.notna(last_observation):

                forecast_start = (
                    last_observation + pd.Timedelta(weeks=1)
                ).date()

                forecast_end = (
                    last_observation + pd.Timedelta(weeks=horizon)
                ).date()

                st.caption(
                    f"Forecast period: {forecast_start} – {forecast_end}"
                )

            else:

                st.warning("No observations in the selected period.")

        except Exception as error:

            st.warning(
                f"Could not load forecasting settings: {error}"
            )

        st.divider()

        # ----------------------------------------------------
        # Initialize weather settings
        # ----------------------------------------------------

        weather_property = None
        weather_values = {}
        color_scale = None

        # ----------------------------------------------------
        # Weather controls
        # ----------------------------------------------------

        if map_layer == "Weather Property":

            weather_property = st.selectbox(
                "Weather property",
                ["Temperature", "Precipitation"],
                key="weather_property"
            )

            weather_df = load_weather_data()

            if weather_df.empty:

                st.warning("No weather data available.")
                st.stop()

            # Available weather period
            min_weather_date = weather_df["time"].min().date()
            max_weather_date = weather_df["time"].max().date()

            # Use the shared training period
            start_date = st.session_state.training_start
            end_date = st.session_state.training_end

            st.caption(
            f"Selected period: {start_date} – {end_date}"
        )

            st.caption(
            f"Available map weather data: "
            f"{min_weather_date} – {max_weather_date}"
        )

            # Check weather data coverage
            if (
                end_date < min_weather_date
                or start_date > max_weather_date
            ):

                st.warning(
                    "No map weather data is available "
                    "for the selected training period."
                )

            elif (
                start_date < min_weather_date
                or end_date > max_weather_date
            ):

                st.warning(
                    "Weather data only covers part of the "
                    "selected training period. The map displays "
                    "aggregated values from available observations."
                )

                st.caption(
                    f"Effective weather period: "
                    f"{max(start_date, min_weather_date)} – "
                    f"{min(end_date, max_weather_date)}"
                )
                    

    # --------------------------------------------------------
    # 5.4 Select geographical boundaries
    # --------------------------------------------------------

    if map_layer == "Weather Property":
        geojson = load_weather_regions()
        layer_name = "Weather Regions"
        region_label = "Weather region"

    else:
        geojson = load_price_areas()
        layer_name = "Price Areas"
        region_label = "Price area"

    regions = sorted({
        feature["properties"]["region"]
        for feature in geojson["features"]
    })

    # Reset region if it does not exist in the new layer
    if st.session_state.selected_region not in regions:
        st.session_state.selected_region = regions[0]

    # --------------------------------------------------------
    # 5.5 Region selector
    # --------------------------------------------------------

    with col_selector:

        st.selectbox(
            "Select region",
            options=regions,
            key="selected_region"
        )

        st.info(
            f"Selected region: {st.session_state.selected_region}"
        )

        if map_layer == "Water Area":
            st.warning(
                "Water area boundaries are not connected yet. "
                "Showing price areas temporarily."
            )

    # --------------------------------------------------------
    # 5.6 Weather values and colour scale
    # --------------------------------------------------------

    if map_layer == "Weather Property":

        weather_df = load_weather_data()

        weather_values = aggregate_weather(
            weather_df,
            start_date,
            end_date,
            weather_property
        )

        # Only use regions present in the current GeoJSON
        weather_values = {
            region: value
            for region, value in weather_values.items()
            if region in regions and pd.notna(value)
        }

        if weather_values:

            values = list(weather_values.values())

            if weather_property == "Temperature":
                min_value = -40
                max_value = 40

                colors = [
                    "#2166AC",
                    "#67A9CF",
                    "#F7F7F7",
                    "#EF8A62",
                    "#B2182B"
                ]

                unit = "°C"

            else:
                min_value = 0
                max_value = max(max(values), 1)

                # Light to dark blue for precipitation
                colors = [
                    "#EFF6FF",
                    "#93C5FD",
                    "#3B82F6",
                    "#1D4ED8",
                    "#1E3A8A"
                ]

                unit = "mm"

            color_scale = cm.LinearColormap(
                colors=colors,
                vmin=min_value,
                vmax=max_value
            )

            color_scale.caption = (
                f"{weather_property} ({unit})"
            )

        with col_selector:

            if weather_values:
                st.caption(
                    "Weather data available for: "
                    + ", ".join(sorted(weather_values))
                )
            else:
                st.warning(
                    "No aggregated weather data available "
                    "for these regions and dates."
                )

    # --------------------------------------------------------
    # 5.7 Polygon styling
    # --------------------------------------------------------

    selected_region = st.session_state.selected_region

    def style_function(feature):
        """Style regions according to layer and selected values."""

        region = feature["properties"]["region"]

        is_selected = region == selected_region

        if map_layer == "Weather Property":

            if region in weather_values and color_scale is not None:
                fill_color = color_scale(weather_values[region])
                opacity = 0.7

            else:
                fill_color = "#D1D5DB"
                opacity = 0.4

        else:
            fill_color = "#93C5FD"
            opacity = 0.35

        return {
            "fillColor": fill_color,
            "color": "#1D4ED8" if is_selected else "#475569",
            "weight": 4 if is_selected else 1,
            "fillOpacity": opacity
        }

    # --------------------------------------------------------
    # 5.8 Create map
    # --------------------------------------------------------

    with col_map:

        st.subheader("Interactive Map")

        m = folium.Map(
            location=[64.5, 12.0],
            zoom_start=5,
            tiles="OpenStreetMap"
        )

        folium.GeoJson(
            geojson,
            name=layer_name,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=["region"],
                aliases=[f"{region_label}:"]
            )
        ).add_to(m)

        if color_scale is not None:
            color_scale.add_to(m)

        map_data = st_folium(
            m,
            height=480,
            width=None,
            key=f"interactive_map_{map_layer}"
        )

    # --------------------------------------------------------
    # 5.9 Handle map clicks
    # --------------------------------------------------------

    if map_data:

        clicked_feature = map_data.get("last_active_drawing")

        if clicked_feature:

            clicked_region = (
                clicked_feature
                .get("properties", {})
                .get("region")
            )

            if (
                clicked_region in regions
                and clicked_region != st.session_state.selected_region
            ):
                st.session_state.selected_region = clicked_region
                st.rerun()
