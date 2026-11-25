import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from scipy.fft import dct, idct
from scipy.signal import spectrogram
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL


# High-pass filter using DCT
def dct_highpass_filter(values, cutoff=30):
    """
    Remove low-frequency variations using DCT.

    """

    values = np.asarray(values, dtype=float)

    if not 0 <= cutoff < len(values):
        raise ValueError("cutoff must be between 0 and len(values)-1")

    if not np.isfinite(values).all():
        raise ValueError("Input contains missing or infinite values")

    # Transform the signal into frequency components
    coefficients = dct(values, type=2, norm="ortho")

    # Remove low-frequency components, frequency is considered low if it is below the cutoff frequency
    coefficients[:cutoff] = 0

    # Reconstruct the high-frequency signal
    filtered = idct(coefficients, type=2, norm="ortho")

    return filtered


def plot_weather_spc(
    df,
    region="NO3",
    weather_property="Temperature",
    cutoff=30,
    n_std=3
):
    """
    Detect weather anomalies using DCT high-pass filtering
    and robust SPC limits.

    Supports temperature and precipitation.
    """

    # Select weather variable
    properties = {
        "Temperature": ("temperature_mean", "Temperature (°C)"),
        "Precipitation": ("precipitation_mean", "Precipitation (mm/hour)")
    }

    if weather_property not in properties:
        raise ValueError("Invalid weather property")

    column, ylabel = properties[weather_property]

    data = df.sort_values("time").copy()
    data = data.dropna(subset=[column])

    values = data[column].to_numpy(dtype=float)

    # Remove low-frequency variations
    satv = dct_highpass_filter(values, cutoff=cutoff)

    # Robust statistics
    median = np.median(satv)
    mad = np.median(np.abs(satv - median))
    robust_std = 1.4826 * mad

    # SPC limits
    lower_limit = median - n_std * robust_std
    upper_limit = median + n_std * robust_std

    # Identify anomalies
    outliers = (satv < lower_limit) | (satv > upper_limit)

    # Convert SPC limits to original scale
    baseline = values - satv

    lower_curve = baseline + lower_limit
    upper_curve = baseline + upper_limit

    # Interactive Plotly figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data["time"],
        y=values,
        mode="lines",
        name=weather_property,
        line=dict(color="steelblue", width=1)
    ))

    fig.add_trace(go.Scatter(
        x=data["time"],
        y=upper_curve,
        mode="lines",
        name="Upper SPC limit",
        line=dict(color="darkorange", dash="dash")
    ))

    fig.add_trace(go.Scatter(
        x=data["time"],
        y=lower_curve,
        mode="lines",
        name="Lower SPC limit",
        line=dict(color="green", dash="dash")
    ))

    fig.add_trace(go.Scatter(
        x=data.loc[outliers, "time"],
        y=values[outliers],
        mode="markers",
        name="Anomalies",
        marker=dict(color="red", size=6)
    ))

    fig.update_layout(
        title=f"{weather_property} SPC Analysis – {region}",
        xaxis_title="Date",
        yaxis_title=ylabel,
        template="plotly_white",
        hovermode="x unified",
        height=450
    )

    summary = {
        "weather_property": weather_property,
        "cutoff": cutoff,
        "n_std": n_std,
        "median_satv": float(median),
        "robust_std": float(robust_std),
        "lower_limit_satv": float(lower_limit),
        "upper_limit_satv": float(upper_limit),
        "n_observations": len(data),
        "n_outliers": int(outliers.sum()),
        "outlier_percentage": float(100 * outliers.mean())
    }

    return fig, summary


# Plot weather with LOF anomalies
def plot_weather_lof(
    df,
    region="NO3",
    weather_property="Temperature",
    contamination=0.01,
    n_neighbors=20
):
    """
    Detect weather anomalies using Local Outlier Factor.

    Supports temperature and precipitation.
    """

    # Select weather variable
    properties = {
        "Temperature": ("temperature_mean", "Temperature (°C)"),
        "Precipitation": ("precipitation_mean", "Precipitation (mm/hour)")
    }

    if weather_property not in properties:
        raise ValueError("Invalid weather property")

    column, ylabel = properties[weather_property]

    # Prepare data
    data = df.sort_values("time").copy()
    data = data.dropna(subset=[column])

    values = data[column].to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError("Weather data contains infinite values")

    if not 0 < contamination <= 0.5:
        raise ValueError("contamination must be between 0 and 0.5")

    if not 1 <= n_neighbors < len(values):
        raise ValueError("n_neighbors must be smaller than the number of observations")

    # LOF expects a two-dimensional feature matrix
    X = values.reshape(-1, 1)

    # Initialize LOF model
    lof = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination
    )

    # Detect anomalies
    labels = lof.fit_predict(X)

    outliers = labels == -1

    # Create interactive Plotly figure
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data["time"],
        y=values,
        mode="lines",
        name=weather_property,
        line=dict(color="steelblue", width=1)
    ))

    fig.add_trace(go.Scatter(
        x=data.loc[outliers, "time"],
        y=values[outliers],
        mode="markers",
        name="LOF anomalies",
        marker=dict(color="red", size=6)
    ))

    fig.update_layout(
        title=f"{weather_property} LOF Anomaly Detection – {region}",
        xaxis_title="Date",
        yaxis_title=ylabel,
        template="plotly_white",
        hovermode="closest",
        height=450
    )

    # Summary statistics
    summary = {
        "weather_property": weather_property,
        "n_observations": len(data),
        "mean": float(np.mean(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "n_outliers": int(outliers.sum()),
        "outlier_percentage": float(outliers.mean() * 100),
        "contamination": contamination,
        "n_neighbors": n_neighbors
    }

    return fig, summary


# Plot STL decomposition of reservoir filling degree
def plot_filling_stl(
    df,
    date_col,
    value_col,
    period=52,
    seasonal=13,
    trend=105,
    robust=True
):
    """
    Perform STL decomposition on reservoir filling degree
    and visualize the components using Plotly.
    """

    # Prepare time series
    data = df[[date_col, value_col]].copy()

    data[date_col] = pd.to_datetime(data[date_col])

    data = (
        data
        .sort_values(date_col)
        .set_index(date_col)
    )

    series = data[value_col].astype(float)

    if series.isna().any():
        raise ValueError("Filling degree contains missing values")

    # Perform STL decomposition
    stl = STL(
        series,
        period=period,
        seasonal=seasonal,
        trend=trend,
        robust=robust
    )

    result = stl.fit()

    # ========================================================
    # INTERACTIVE PLOTLY FIGURE
    # ========================================================

    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=[
            "Observed",
            "Trend",
            "Seasonal",
            "Residual"
        ]
    )

    components = [
        ("Observed", series, "#397D73"),
        ("Trend", result.trend, "#2563EB"),
        ("Seasonal", result.seasonal, "#D97706"),
        ("Residual", result.resid, "#64748B")
    ]

    for row, (name, values, color) in enumerate(
        components, start=1
    ):

        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=values,
                mode="lines",
                name=name,
                line=dict(
                    color=color,
                    width=1.5
                ),
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>"
                    "%{y:.3f}"
                    "<extra></extra>"
                )
            ),
            row=row,
            col=1
        )

        fig.update_yaxes(
            title_text=name,
            row=row,
            col=1
        )

    # Zero reference lines
    for row in [3, 4]:

        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="gray",
            opacity=0.5,
            row=row,
            col=1
        )

    fig.update_xaxes(
        title_text="Date",
        row=4,
        col=1
    )

    fig.update_layout(
        title="STL Decomposition of Reservoir Filling Degree",
        height=850,
        showlegend=False,
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=30, t=80, b=40)
    )

    # Summary statistics
    summary = {
        "n_observations": len(series),
        "period": period,
        "seasonal": seasonal,
        "trend": trend,
        "robust": robust,
        "mean_filling": float(series.mean()),
        "min_filling": float(series.min()),
        "max_filling": float(series.max()),
        "residual_std": float(result.resid.std())
    }

    return fig, summary


# Plot spectrogram of reservoir filling degree
def plot_filling_spectrogram(
    df,
    date_col="dato_Id",
    value_col="fyllingsgrad",
    window_length=156,
    overlap=130
):
    """
    Plot an interactive spectrogram of weekly
    reservoir filling degree.
    """

    data = df.sort_values(date_col).copy()

    values = data[value_col].to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError("Filling degree contains missing values")

    if not 0 <= overlap < window_length <= len(values):
        raise ValueError("Invalid window length or overlap")

    # Sampling frequency: one observation per week
    frequencies, times, power = spectrogram(
        values,
        fs=1.0,
        nperseg=window_length,
        noverlap=overlap,
        detrend="linear",
        scaling="spectrum"
    )

    # Convert window positions to calendar dates
    dates = pd.to_datetime(
        data[date_col]
    ).reset_index(drop=True)

    time_indices = np.clip(
        np.round(times).astype(int),
        0,
        len(dates) - 1
    )

    spectrogram_dates = dates.iloc[time_indices]

    # Convert power to decibels
    power_db = 10 * np.log10(power + 1e-12)

    # ========================================================
    # INTERACTIVE PLOTLY HEATMAP
    # ========================================================

    fig = go.Figure()

    fig.add_trace(
        go.Heatmap(
            x=spectrogram_dates,
            y=frequencies,
            z=power_db,
            colorscale="Viridis",
            colorbar=dict(
                title="Power (dB)"
            ),
            hovertemplate=(
                "Date: %{x|%Y-%m-%d}<br>"
                "Frequency: %{y:.4f} cycles/week<br>"
                "Power: %{z:.2f} dB"
                "<extra></extra>"
            )
        )
    )

    # Mark the annual frequency
    fig.add_hline(
        y=1 / 52,
        line_color="red",
        line_dash="dash",
        line_width=2,
        annotation_text="Annual cycle (52 weeks)",
        annotation_position="top left",
        annotation_font_color="red"
    )

    fig.update_layout(
        title="Spectrogram of Reservoir Filling Degree",
        xaxis_title="Date",
        yaxis_title="Frequency (cycles/week)",
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=30, t=60, b=40)
    )

    summary = {
        "n_observations": len(values),
        "window_length": window_length,
        "overlap": overlap,
        "n_time_windows": len(times),
        "n_frequencies": len(frequencies)
    }

    return fig, summary


# ============================================================
# SLIDING WINDOW CORRELATION
# ============================================================

def plot_sliding_correlation(
    df,
    weather_property="Temperature",
    window=12,
    lag=0
):
    """
    Calculate rolling Pearson correlation between
    weekly weather and reservoir filling degree.

    Positive lag means weather leads reservoir filling.
    """

    properties = {
        "Temperature": ("temperature_mean", "Temperature"),
        "Precipitation": ("precipitation_mean", "Precipitation")
    }

    weather_col, weather_label = properties[weather_property]

    data = df.sort_values("date").copy()

    # Shift weather values to compare earlier weather
    # with later reservoir filling
    data["weather_lagged"] = data[weather_col].shift(lag)

    # Rolling Pearson correlation
    data["correlation"] = (
        data["weather_lagged"]
        .rolling(window=window, min_periods=window)
        .corr(data["fyllingsgrad"])
    )

    # Create interactive Plotly chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data["date"],
        y=data["correlation"],
        mode="lines",
        name="Rolling correlation",
        line=dict(color="steelblue", width=2)
    ))

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray"
    )

    fig.update_layout(
        title=f"Sliding Window Correlation – {weather_label}",
        xaxis_title="Date",
        yaxis_title="Pearson correlation",
        yaxis_range=[-1, 1],
        template="plotly_white",
        height=450
    )

    return fig, data