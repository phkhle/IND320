import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.forecasting import (
    forecast_reservoir_snarimax,
    forecast_reservoir_intervals
)


from src.forecast_controls import (
    DEFAULT_CONFIG,
    get_available_data,
    show_training_period,
    show_forecast_horizon
)



st.title("Reservoir Filling Forecast")

st.write(
    """
    Forecast future reservoir filling using SNARIMAX
    from the River machine learning framework.
    """
)

st.info(
    "Forecasting is currently only available for NO3, "
    "as model development and validation in Assignment 4 "
    "were conducted for this price area."
)


st.divider()


with st.expander("Recommended Model Configuration"):

    st.markdown("""
    The default model configuration is based on the
    validation experiments conducted in Assignment 4.

    Users can freely modify the model parameters,
    training period, forecast horizon and exogenous
    variables to explore alternative configurations.

    Alternative configurations may produce different
    forecasting performance and have not necessarily
    been validated.
    """)

# ============================================================
# 1. FORECAST CONFIGURATION
# ============================================================

st.header("Forecast Configuration")

def update_default_mode():

    st.session_state.use_default_forecast = (
        st.session_state.default_forecast_widget
    )


st.session_state.default_forecast_widget = (
    st.session_state.use_default_forecast
)

use_default = st.checkbox(
    "Use recommended model configuration",
    key="default_forecast_widget",
    on_change=update_default_mode
)

if use_default:

    st.info(
        "Using the recommended model configuration "
        "based on Assignment 4 validation results."
    )
    st.session_state.training_start = (
        DEFAULT_CONFIG["training_start"]
    )

    st.session_state.training_end = (
        DEFAULT_CONFIG["training_end"]
    )

    st.session_state.forecast_exog_cols = (
        DEFAULT_CONFIG["exog_cols"].copy()
    )

    for param in ["p", "d", "q", "m", "sp", "sd", "sq", "horizon"]:

        st.session_state[f"forecast_{param}"] = (
            DEFAULT_CONFIG[param]
        )
else:

    st.caption(
        "Custom configuration. "
        "You can modify all forecasting settings."
    )


region = st.selectbox(
    "Price region",
    options=["NO3"]
)


# ============================================================
# 2. EXOGENOUS VARIABLES
# ============================================================

st.subheader("Exogenous Variables")

if "forecast_exog_cols" not in st.session_state:

    st.session_state.forecast_exog_cols = [
        "temperature_mean"
    ]


def update_exog_cols():

    st.session_state.forecast_exog_cols = (
        st.session_state.forecast_exog_widget
    )


st.session_state.forecast_exog_widget = (
    st.session_state.forecast_exog_cols
)

exog_cols = st.multiselect(
    "Select external weather variables",
    options=[
        "temperature_mean",
        "precipitation_sum"
    ],
    key="forecast_exog_widget",
    on_change=update_exog_cols,
    disabled=use_default,
    format_func=lambda x: {
        "temperature_mean": "Temperature",
        "precipitation_sum": "Precipitation"
    }[x]
)

if exog_cols:

    st.caption(
        "Future weather is estimated using historical "
        "weekly averages."
    )

else:

    st.caption(
        "Forecasting without exogenous variables."
    )

if exog_cols:

    st.info(
        "Historical weather data is currently available "
        "until 15 November 2026. "
        "Forecasts start from the last selected training "
        "observation. Future weather values are estimated "
        "using historical weekly averages."
    )

else:

    st.info(
        "Without weather variables, the training period "
        "can extend to the latest available reservoir "
        "observation from the NVE API."
    )

# ============================================================
# 3. AVAILABLE DATA
# ============================================================

try:

    df_available = get_available_data(
        region=region,
        exog_cols=exog_cols
    )

except Exception as error:

    st.error(f"Could not load data: {error}")
    st.stop()


# ============================================================
# 4. TRAINING PERIOD AND FORECAST HORIZON
# ============================================================

st.subheader("Training Period and Forecast Horizon")

col1, col2 = st.columns(2)

with col1:

    training_start, training_end = show_training_period(
        df=df_available,
        prefix="forecast",
        disabled=use_default
    )

with col2:

    horizon = show_forecast_horizon(
        prefix="forecast",
        disabled=use_default
    )


# Select training data
df_train = df_available.loc[
    (df_available["dato_Id"] >= pd.Timestamp(training_start)) &
    (df_available["dato_Id"] <= pd.Timestamp(training_end))
].copy()

n_weeks = len(df_train)

st.caption(
    f"Selected training history: {n_weeks} weekly observations "
    f"({n_weeks / 52:.1f} years)"
)

# ============================================================
# 5. MODEL PARAMETERS
# ============================================================

st.subheader("SNARIMAX Parameters")

# Initialize parameters if they do not exist
for param in ["p", "d", "q", "m", "sp", "sd", "sq"]:

    key = f"forecast_{param}"

    if key not in st.session_state:

        st.session_state[key] = DEFAULT_CONFIG[param]


with st.expander("Advanced model settings"):

    col1, col2, col3 = st.columns(3)

    with col1:

        p = st.number_input(
            "p",
            min_value=0,
            max_value=5,
            key="forecast_p",
            disabled=use_default
        )

        d = st.number_input(
            "d",
            min_value=0,
            max_value=2,
            key="forecast_d",
            disabled=use_default
        )

        q = st.number_input(
            "q",
            min_value=0,
            max_value=5,
            key="forecast_q",
            disabled=use_default
        )

    with col2:

        m = st.number_input(
            "m",
            min_value=1,
            max_value=104,
            key="forecast_m",
            disabled=use_default
        )

        sp = st.number_input(
            "sp",
            min_value=0,
            max_value=3,
            key="forecast_sp",
            disabled=use_default
        )

    with col3:

        sd = st.number_input(
            "sd",
            min_value=0,
            max_value=2,
            key="forecast_sd",
            disabled=use_default
        )

        sq = st.number_input(
            "sq",
            min_value=0,
            max_value=3,
            key="forecast_sq",
            disabled=use_default
        )

# ============================================================
# 6. VALIDATE TRAINING PERIOD
# ============================================================

min_required_weeks = max(
    104,
    m * max(sp, sd, sq) + 2
)

valid_training = n_weeks >= min_required_weeks

if not valid_training:

    st.warning(
        f"The selected model requires at least "
        f"{min_required_weeks} weekly observations. "
        f"Currently selected: {n_weeks}."
    )

# Check for missing weeks
elif not df_train.empty:

    expected_dates = pd.date_range(
        start=df_train["dato_Id"].min(),
        end=df_train["dato_Id"].max(),
        freq="7D"
    )

    missing_dates = expected_dates.difference(
        df_train["dato_Id"]
    )

    if len(missing_dates) > 0:

        valid_training = False

        st.warning(
            f"The selected period contains "
            f"{len(missing_dates)} missing weeks."
        )


# ============================================================
# PREDICTION INTERVAL SETTINGS
# ============================================================

st.subheader("Prediction Intervals")

show_intervals = st.checkbox(
    "Show prediction intervals",
    value=False
)

confidence = st.selectbox(
    "Confidence level",
    options=[0.80, 0.90, 0.95],
    index=1,
    format_func=lambda x: f"{x:.0%}",
    disabled=not show_intervals
)

# ============================================================
# 7. CURRENT FORECAST CONFIGURATION
# ============================================================

current_config = (
    region,
    training_start,
    training_end,
    horizon,
    p, d, q,
    m, sp, sd, sq,
    tuple(exog_cols),
    show_intervals,
    confidence
)

# Remove outdated forecasts when settings change
if st.session_state.get("forecast_config") != current_config:

    st.session_state.pop("forecast_result", None)
    st.session_state.pop("forecast_history", None)
    st.session_state.pop("forecast_region", None)
    st.session_state.pop("forecast_config", None)


# ============================================================
# 8. RUN FORECAST
# ============================================================

st.divider()

if st.button(
    "Generate Forecast",
    type="primary",
    disabled=not valid_training
):

    try:

        with st.spinner("Generating forecast..."):

            forecast_params = dict(
                df=df_train,
                horizon=horizon,
                p=p,
                d=d,
                q=q,
                m=m,
                sp=sp,
                sd=sd,
                sq=sq,
                exog_cols=exog_cols,
                weather_history_years=5
            )

            if show_intervals:

                forecast = forecast_reservoir_intervals(
                    confidence=confidence,
                    **forecast_params
                )

            else:

                forecast = forecast_reservoir_snarimax(
                    **forecast_params
                )

            st.session_state.forecast_result = forecast
            st.session_state.forecast_history = df_train
            st.session_state.forecast_region = region
            st.session_state.forecast_config = current_config

        st.success("Forecast generated successfully.")

    except Exception as error:

        st.session_state.pop("forecast_result", None)
        st.session_state.pop("forecast_history", None)
        st.session_state.pop("forecast_config", None)

        st.error(f"Forecast failed: {error}")

# ============================================================
# ANIMATED FORECAST VISUALIZATION
# ============================================================

if "forecast_result" in st.session_state:

    forecast = st.session_state.forecast_result
    history = st.session_state.forecast_history

    st.header("Forecast Results")

    # Display the last 100 weeks of training data
    history_plot = history.tail(260)

    # Connect historical observations and forecast
    forecast_plot = pd.concat(
        [
            history[["dato_Id", "fyllingsgrad"]]
            .tail(1)
            .rename(columns={
                "dato_Id": "date",
                "fyllingsgrad": "predicted"
            }),
            forecast
        ],
        ignore_index=True
    )

    fig = go.Figure()

    # Historical observations
    fig.add_trace(
        go.Scatter(
            x=history_plot["dato_Id"],
            y=history_plot["fyllingsgrad"] * 100,
            mode="lines",
            name="Historical observations",
            line=dict(color="steelblue")
        )
    )

    # Display the complete forecast by default
    fig.add_trace(
        go.Scatter(
            x=forecast_plot["date"],
            y=forecast_plot["predicted"] * 100,
            mode="lines+markers",
            name="Forecast",
            line=dict(
                color="#E9A23B",
                dash="dash",
                width=2.5
            )
        )
    )


    # Prediction intervals
    if show_intervals:

        # Lower boundary
        fig.add_trace(
            go.Scatter(
                x=forecast["date"],
                y=forecast["lower"] * 100,
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip"
            )
        )

        # Upper boundary and shaded interval
        fig.add_trace(
            go.Scatter(
                x=forecast["date"],
                y=forecast["upper"] * 100,
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(233, 162, 59, 0.20)",
                name=f"{confidence:.0%} prediction interval"
            )
        )

    # Animation frames
    frames = []

    for i in range(1, len(forecast_plot)):

        frame_data = [
            go.Scatter(
                x=forecast_plot["date"].iloc[:i + 1],
                y=forecast_plot["predicted"].iloc[:i + 1] * 100
            )
        ]

        trace_indices = [1]

        if show_intervals:

            frame_data.extend([
                go.Scatter(
                    x=forecast["date"].iloc[:i],
                    y=forecast["lower"].iloc[:i] * 100
                ),
                go.Scatter(
                    x=forecast["date"].iloc[:i],
                    y=forecast["upper"].iloc[:i] * 100
                )
            ])

            trace_indices.extend([2, 3])

        frames.append(
            go.Frame(
                data=frame_data,
                traces=trace_indices,
                name=str(i)
            )
        )

    fig.frames = frames

    fig.update_layout(
        paper_bgcolor="#E8EEF2",
        plot_bgcolor="#F0F4F6",
        font=dict(color="#243746"),

        title=(
            f"Reservoir Filling Forecast – "
            f"{st.session_state.forecast_region}"
        ),
        xaxis_title="Date",
        yaxis_title="Reservoir filling (%)",
        xaxis=dict(
            range=[
                history_plot["dato_Id"].min(),
                forecast["date"].max()
            ]
        ),
        yaxis=dict(range=[0, 100]),
        height=500,

        updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    x=0,
                    y=1.15,
                    xanchor="left",
                    yanchor="top",
                    bgcolor="#334155",
                    bordercolor="#64748B",
                    borderwidth=1,
                    font=dict(
                        color="#FFFFFF",
                        size=13
                    ),
                    showactive=False,

                    buttons=[
                        dict(
                            label="▶ Play Forecast",
                            method="animate",
                            args=[
                                None,
                                {
                                    "frame": {
                                        "duration": 300,
                                        "redraw": True
                                    },
                                    "transition": {"duration": 0},
                                    "fromcurrent": False
                                }
                            ]
                        ),
                        dict(
                            label="Reset",
                            method="animate",
                            args=[
                                [str(len(forecast_plot) - 1)],
                                {
                                    "mode": "immediate",
                                    "frame": {
                                        "duration": 0,
                                        "redraw": True
                                    },
                                    "transition": {"duration": 0}
                                }
                            ]
                        )
                    ]
                )
]
    )

    st.plotly_chart(fig, use_container_width=True)
    if show_intervals:

        st.caption(
            "Prediction intervals are estimated using Quantile Loss. "
            "The intervals are experimental and their empirical "
            "coverage has not been validated."
        )

        if (
            (forecast["lower"] < 0).any()
            or (forecast["upper"] > 1).any()
        ):
            st.warning(
                "Some interval boundaries exceed the physical "
                "range of reservoir filling (0–100%)."
            )
    st.subheader("Predicted Reservoir Filling")

    forecast_table = forecast.copy()

    column_names = {
        "predicted": "Predicted filling (%)",
        "lower": "Lower boundary (%)",
        "upper": "Upper boundary (%)"
    }

    for col in column_names:

        if col in forecast_table.columns:
            forecast_table[col] = (
                forecast_table[col] * 100
            ).round(2)

    forecast_table = forecast_table.rename(
        columns=column_names
    )

    st.dataframe(
        forecast_table,
        use_container_width=True,
        hide_index=True
    )