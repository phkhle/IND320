
import json
from pathlib import Path

import folium
import streamlit as st
from streamlit_folium import st_folium
import branca.colormap as cm
import pandas as pd


# Path relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GEOJSON_PATH = PROJECT_ROOT / "data" / "price_areas.geojson"


@st.cache_data
def load_price_areas():
    """Load the electricity price area polygons."""
    with open(GEOJSON_PATH, encoding="utf-8") as file:
        return json.load(file)

def load_weather_data():
    """
    Load hourly aggregated ERA5 weather data for available regions.
    """

    weather_dir = PROJECT_ROOT / "data" / "weather"

    datasets = []

    for region in ["NO2", "NO3"]:
        file_path = weather_dir / f"{region}_hourly_mean_2024.parquet"

        if file_path.exists():
            df = pd.read_parquet(file_path)

            df["region"] = region
            df["time"] = pd.to_datetime(df["time"], utc=True)

            datasets.append(df)

    if not datasets:
        return pd.DataFrame()

    return pd.concat(datasets, ignore_index=True)



def aggregate_weather(df, start_date, end_date, property_name):
    """
    Aggregate weather observations by region for a selected period.
    
    """

    df = df.copy()

    start = pd.Timestamp(start_date).tz_localize("UTC")
    end = pd.Timestamp(end_date).tz_localize("UTC") + pd.Timedelta(days=1)

    df = df[
        (df["time"] >= start) &
        (df["time"] < end)
    ]

    if property_name == "Temperature":
        result = df.groupby("region")["temperature_mean"].mean()

    else:
        # Sum hourly spatial mean precipitation over the selected period
        result = df.groupby("region")["precipitation_mean"].sum()

    return result.to_dict()





def show_interactive_map():
    """
    Display an interactive map with selectable map layers,
    weather properties, time periods and shared region selection.
    """

    geojson = load_price_areas()
    weather_df = load_weather_data()

    regions = sorted({
        feature["properties"]["region"]
        for feature in geojson["features"]
    })

    # Initialize shared session state
    if "map_layer" not in st.session_state:
        st.session_state.map_layer = "Price Area"

    if "selected_region" not in st.session_state:
        st.session_state.selected_region = "NO1"

    if st.session_state.selected_region not in regions:
        st.session_state.selected_region = regions[0]

    # Layout: map on the left, controls on the right
    col_map, col_selector = st.columns([3, 1])

    # ========================================================
    # 1. MAP CONTROLS
    # ========================================================

    with col_selector:
        st.subheader("Area Selection")

        st.selectbox(
            "Select map layer",
            ["Price Area", "Water Area", "Weather Property"],
            key="map_layer"
        )

        weather_values = {}
        color_scale = None
        weather_property = None

        if st.session_state.map_layer == "Weather Property":

            weather_property = st.selectbox(
                "Weather property",
                ["Temperature", "Precipitation"],
                key="weather_property"
            )

            start_date = st.date_input(
                "Start date",
                value=pd.Timestamp("2024-01-01").date(),
                key="weather_start"
            )

            end_date = st.date_input(
                "End date",
                value=pd.Timestamp("2024-01-31").date(),
                key="weather_end"
            )

            if start_date > end_date:
                st.error("Start date must be before end date.")
                st.stop()

            if weather_df.empty:
                st.warning("No weather data available.")

            else:
                weather_values = aggregate_weather(
                    weather_df,
                    start_date,
                    end_date,
                    weather_property
                )

                if weather_values:
                    values = list(weather_values.values())
                    if weather_property == "Temperature":
                        min_value = -20
                        max_value = 30
                    else:
                        min_value = 0
                        max_value = max(values) if max(values) > 0 else 1

                    # Create a colour scale for weather values
                    color_scale = cm.LinearColormap(
                        colors=[
                            "#2166AC",
                            "#67A9CF",
                            "#F7F7F7",
                            "#EF8A62",
                            "#B2182B"
                        ],
                        vmin=min_value,
                        vmax=max_value
                    )

                    unit = (
                        "°C"
                        if weather_property == "Temperature"
                        else "mm"
                    )

                    color_scale.caption = (
                        f"{weather_property} ({unit})"
                    )

        elif st.session_state.map_layer == "Water Area":
            st.info("Water area data will be added later.")

        st.selectbox(
            "Select price area",
            options=regions,
            key="selected_region"
        )

        st.info(
            f"Selected region: {st.session_state.selected_region}"
        )

        if st.session_state.map_layer == "Weather Property":
            st.caption(
                "Weather data currently available for NO2 and NO3."
            )

    # ========================================================
    # 2. MAP STYLING
    # ========================================================

    selected_region = st.session_state.selected_region
    map_layer = st.session_state.map_layer

    def style_function(feature):
        """Style each polygon according to the selected map layer."""

        region = feature["properties"]["region"]
        is_selected = region == selected_region

        # Default appearance for price areas
        fill_color = "#93C5FD"

        if map_layer == "Weather Property":

            if region in weather_values and color_scale is not None:
                fill_color = color_scale(weather_values[region])
            else:
                # Grey indicates missing weather data
                fill_color = "#D1D5DB"

        return {
            "fillColor": fill_color,
            "color": "#1D4ED8" if is_selected else "#475569",
            "weight": 4 if is_selected else 1,
            "fillOpacity": 0.65 if region in weather_values else 0.35,
        }

    # ========================================================
    # 3. INTERACTIVE MAP
    # ========================================================

    with col_map:
        st.subheader("Interactive Map")

        m = folium.Map(
            location=[64.5, 12.0],
            zoom_start=5,
            tiles="CartoDB positron"
        )

        folium.GeoJson(
            geojson,
            name="Price Areas",
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=["region"],
                aliases=["Price area:"]
            )
        ).add_to(m)

        # Add colour legend when weather data is displayed
        if color_scale is not None:
            color_scale.add_to(m)

        map_data = st_folium(
            m,
            height=480,
            width=None,
            key="price_area_map"
        )

    # ========================================================
    # 4. HANDLE MAP CLICKS
    # ========================================================

    if map_data:
        clicked_feature = map_data.get("last_active_drawing")

        if clicked_feature:
            clicked_region = (
                clicked_feature.get("properties", {}).get("region")
            )

            if clicked_region in regions:
                if clicked_region != st.session_state.selected_region:
                    st.session_state.selected_region = clicked_region
                    st.rerun()
