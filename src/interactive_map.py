
import json
from pathlib import Path

import folium
import streamlit as st
import pandas as pd
import branca.colormap as cm

from streamlit_folium import st_folium

from src.forecast_controls import (
    get_available_data,
    show_training_period
)

from src.area_selector import (
    get_selected_area,
    set_selected_area,
    format_area_name,
    WATER_AREAS
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

    st.header("Explore Norwegian Energy Regions")

    # --------------------------------------------------------
    # 5.1 Initialize shared area selection
    # --------------------------------------------------------

    area_type, area_number = get_selected_area()

    if "map_layer_preference" not in st.session_state:
        st.session_state.map_layer_preference = "Price Area"

    map_layer = st.session_state.map_layer_preference

    if area_type == "EL":
        map_layer = "Price Area"

    elif area_type == "VASS":

        if map_layer != "Weather Property":
            map_layer = "Water Area"

    st.session_state["_map_layer_widget"] = map_layer

    # --------------------------------------------------------
    # 5.2 Map layout
    # --------------------------------------------------------

    col_map, col_selector = st.columns(
        [3, 1.3],
        gap="large"
    )

    # --------------------------------------------------------
    # 5.3 Map layer selection
    # --------------------------------------------------------

    with col_selector:

        st.subheader("Map Settings")

        def update_map_layer():

            new_layer = st.session_state["_map_layer_widget"]

            st.session_state.map_layer_preference = new_layer

            current_type, current_number = get_selected_area()

            if new_layer == "Price Area":

                if current_type != "EL":
                    set_selected_area("EL", 3)

            else:

                if current_type != "VASS":
                    set_selected_area("VASS", 1)

        map_layer = st.selectbox(
            "Colour by",
            options=[
                "Price Area",
                "Water Area",
                "Weather Property"
            ],
            key="_map_layer_widget",
            on_change=update_map_layer
        )

    # --------------------------------------------------------
    # 5.4 Select geographical boundaries
    # --------------------------------------------------------

    if map_layer == "Price Area":

        geojson = load_price_areas()
        layer_name = "Price Areas"
        region_label = "Price area"

    elif map_layer == "Water Area":

        geojson = load_weather_regions()
        layer_name = "Water Areas"
        region_label = "Water area"

    else:

        geojson = load_weather_regions()
        layer_name = "Weather Regions"
        region_label = "Weather region"

    regions = sorted({
        feature["properties"]["region"]
        for feature in geojson["features"]
    })

    area_type, area_number = get_selected_area()

    if map_layer == "Price Area":

        region_mapping = {
            region: int(region.replace("NO", "").strip())
            for region in regions
        }

        map_area_type = "EL"

    else:

        region_mapping = {
            name: number
            for number, name in WATER_AREAS.items()
        }

        map_area_type = "VASS"

    selected_region = None

    if area_type == map_area_type:

        selected_region = next(
            (
                region
                for region, number in region_mapping.items()
                if number == area_number
                and region in regions
            ),
            None
        )

    # --------------------------------------------------------
    # 5.5 Region selection
    # --------------------------------------------------------

    with col_selector:

        st.session_state["_map_region_widget"] = selected_region

        def update_map_region():

            region = st.session_state["_map_region_widget"]

            if region in region_mapping:

                set_selected_area(
                    map_area_type,
                    region_mapping[region]
                )

        st.selectbox(
            "Select region",
            options=regions,
            index=None,
            placeholder="Select a region",
            key="_map_region_widget",
            on_change=update_map_region
        )

        if area_type == "NO":

            st.caption(
                "Select a region to explore regional data."
            )

    # --------------------------------------------------------
    # 5.6 Weather settings
    # --------------------------------------------------------

    weather_property = None
    weather_values = {}
    color_scale = None

    if map_layer == "Weather Property":

        with col_selector:

            weather_property = st.selectbox(
                "Weather property",
                options=[
                    "Temperature",
                    "Precipitation"
                ],
                key="weather_property"
            )

            weather_df = load_weather_data()

            # Only include regions displayed on the map
            if not weather_df.empty:

                weather_df = weather_df[
                    weather_df["region"].isin(regions)
                ].copy()

            if weather_df.empty:

                st.warning("No weather data available.")

            else:

                min_weather_date = (
                    weather_df["time"].min().date()
                )

                max_weather_date = (
                    weather_df["time"].max().date()
                )

                # Independent weather period
                if min_weather_date < max_weather_date:

                    start_date, end_date = st.slider(
                        "Weather period",
                        min_value=min_weather_date,
                        max_value=max_weather_date,
                        value=(
                            min_weather_date,
                            max_weather_date
                        ),
                        format="DD MMM YYYY",
                        key="map_weather_period"
                    )

                else:

                    start_date = min_weather_date
                    end_date = max_weather_date

                weather_values = aggregate_weather(
                    weather_df,
                    start_date,
                    end_date,
                    weather_property
                )

                weather_values = {
                    region: value
                    for region, value in weather_values.items()
                    if region in regions
                    and pd.notna(value)
                }

                if not weather_values:

                    st.warning(
                        "No weather observations for this period."
                    )

                else:

                    st.caption(
                        "Grey areas indicate unavailable weather data."
                    )

    # --------------------------------------------------------
    # 5.7 Weather colour scale
    # --------------------------------------------------------

    if weather_values:

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

            max_value = max(
                max(weather_values.values()),
                1
            )

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

    # --------------------------------------------------------
    # 5.8 Geographical colours
    # --------------------------------------------------------

    price_colors = {
        "NO1": "#60A5FA",
        "NO2": "#F59E0B",
        "NO3": "#34A399",
        "NO4": "#A78BFA",
        "NO5": "#F472B6"
    }

    water_colors = {
        "Øst": "#60A5FA",
        "Vest": "#34A399",
        "Nord": "#A78BFA"
    }

    # --------------------------------------------------------
    # 5.9 Polygon styling
    # --------------------------------------------------------

    def style_function(feature):

        region = feature["properties"]["region"]

        is_selected = region == selected_region

        if map_layer == "Weather Property":

            if (
                region in weather_values
                and color_scale is not None
            ):

                fill_color = color_scale(
                    weather_values[region]
                )

                opacity = 0.7

            else:

                fill_color = "#D1D5DB"
                opacity = 0.4

        elif map_layer == "Price Area":

            fill_color = price_colors.get(
                region.replace(" ", ""),
                "#D1D5DB"
            )

            opacity = 0.45

        else:

            fill_color = water_colors.get(
                region,
                "#D1D5DB"
            )

            opacity = 0.45

        return {
            "fillColor": fill_color,
            "color": (
                "#1D4ED8" if is_selected else "#475569"
            ),
            "weight": 4 if is_selected else 1,
            "fillOpacity": opacity
        }

    # --------------------------------------------------------
    # 5.10 Create interactive map
    # --------------------------------------------------------

    with col_map:

        m = folium.Map(
            location=[64.5, 12.0],
            zoom_start=5,
            tiles="OpenStreetMap"
        )

        geojson_layer = folium.GeoJson(
            geojson,
            name=layer_name,
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=["region"],
                aliases=[f"{region_label}:"]
            )
        ).add_to(m)

        # Automatically fit the geographical boundaries
        m.fit_bounds(geojson_layer.get_bounds())

        if color_scale is not None:
            color_scale.add_to(m)

        def update_map_click():

            map_data = st.session_state.get(map_key, {})

            clicked_feature = (
                map_data.get("last_active_drawing") or {}
            )

            clicked_region = (
                clicked_feature
                .get("properties", {})
                .get("region")
            )

            if clicked_region in region_mapping:

                set_selected_area(
                    map_area_type,
                    region_mapping[clicked_region]
                )

        map_key = (
            f"interactive_map_{map_layer}_"
            f"{area_type}_{area_number}"
        )

        st_folium(
            m,
            height=520,
            width=None,
            key=map_key,
            returned_objects=["last_active_drawing"],
            on_change=update_map_click
        )

    # --------------------------------------------------------
    # 5.11 Shared forecast settings
    # --------------------------------------------------------

    with st.expander("Forecast Settings – NO3"):

        try:

            df_forecast_available = get_available_data(
                region="NO3",
                exog_cols=st.session_state.get(
                    "forecast_exog_cols",
                    ["temperature_mean"]
                )
            )

            forecast_col1, forecast_col2 = st.columns(2)

            with forecast_col1:

                training_start, training_end = (
                    show_training_period(
                        df=df_forecast_available,
                        prefix="map",
                        disabled=False
                    )
                )

            with forecast_col2:

                st.session_state["_map_horizon_widget"] = (
                    st.session_state.forecast_horizon
                )

                def update_horizon():

                    st.session_state.forecast_horizon = (
                        st.session_state["_map_horizon_widget"]
                    )

                    st.session_state.use_default_forecast = False

                horizon = st.slider(
                    "Forecast horizon (weeks)",
                    min_value=1,
                    max_value=26,
                    key="_map_horizon_widget",
                    on_change=update_horizon
                )

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
                        last_observation
                        + pd.Timedelta(weeks=1)
                    ).date()

                    forecast_end = (
                        last_observation
                        + pd.Timedelta(weeks=horizon)
                    ).date()

                    st.caption(
                        f"Forecast period: "
                        f"{forecast_start} – {forecast_end}"
                    )

                else:

                    st.warning(
                        "No observations in the training period."
                    )

        except Exception as error:

            st.warning(
                f"Could not load forecast settings: {error}"
            )

        st.page_link(
            "pages/7_Forecasting.py",
            label="Open Reservoir Filling Forecast",
            icon="🔮"
        )
   