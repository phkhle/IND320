import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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


# PPlot precipitation with SPC limits and outliers
def plot_precipitation_spc(
    df,
    region = "NO3",
    cutoff=30,
    n_std=3,
  
):
    """
    Detect precipitation outliers using DCT and robust SPC.
    """

    data = df.sort_values("time").copy()

    precipitation = data["precipitation_mean"].to_numpy()

    # 1. Remove slow variations using DCT
    satv = dct_highpass_filter(
        precipitation,
        cutoff=cutoff
    )

    # 2. Estimate robust statistics from the full year
    median = np.median(satv)
    mad = np.median(np.abs(satv - median))

    robust_std = 1.4826 * mad

    # 3. Define SPC limits in the filtered domain
    lower_limit = median - n_std * robust_std
    upper_limit = median + n_std * robust_std

    # 4. Identify outliers using SATV
    outliers = (satv < lower_limit) | (satv > upper_limit)

    # 5. Convert SPC limits to original precipitation scale
    baseline = precipitation - satv

    lower_curve = baseline + lower_limit
    upper_curve = baseline + upper_limit

    # 6. Plot original precipitation, not SATV
    fig, ax = plt.subplots(figsize=(15, 5))

    ax.plot(
        data["time"],
        precipitation,
        color="steelblue",
        linewidth=0.7,
        label="Average precipitation"
    )

    ax.plot(
        data["time"],
        upper_curve,
        color="darkorange",
        linestyle="--",
        linewidth=1,
        label="Upper SPC limit"
    )

    ax.plot(
        data["time"],
        lower_curve,
        color="green",
        linestyle="--",
        linewidth=1,
        label="Lower SPC limit"
    )

    ax.scatter(
        data.loc[outliers, "time"],
        precipitation[outliers],
        color="red",
        s=12,
        label="Outliers",
        zorder=3
    )

    ax.set(
        title= f"Precipitation SPC Analysis – {region} (2024)",
        xlabel="Date",
        ylabel="Average precipitation (mm/hour)"
    )

    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()

    summary = {
        "cutoff": cutoff,
        "n_std": n_std,
        "median_satv": median,
        "robust_std": robust_std,
        "lower_limit_satv": lower_limit,
        "upper_limit_satv": upper_limit,
        "n_observations": len(data),
        "n_outliers": int(outliers.sum()),
        "outlier_percentage": 100 * outliers.mean()
    }

    return fig, summary



# Plot temperature with LOF anomalies
def plot_temperature_lof(
    df,
    region = 'NO3',
    contamination=0.01,
    n_neighbors=20,
    
):
    """
    Detect temperature anomalies using Local Outlier Factor.

    """

    data = df.sort_values("time").copy()

    # Extract temperature values
    temperature = data["temperature_mean"].to_numpy()

    if not np.isfinite(temperature).all():
        raise ValueError("Temperature contains missing or infinite values")

    if not 0 < contamination <= 0.5:
        raise ValueError("contamination must be between 0 and 0.5")

    # LOF expects a two-dimensional feature matrix
    X = temperature.reshape(-1, 1)

    # Initialize LOF model
    lof = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination
    )

    # -1 = outlier, 1 = inlier
    labels = lof.fit_predict(X)

    outliers = labels == -1

    # Plot original temperature
    fig, ax = plt.subplots(figsize=(15, 5))

    ax.plot(
        data["time"],
        temperature,
        color="steelblue",
        linewidth=0.8,
        label="Average temperature"
    )

    ax.scatter(
        data.loc[outliers, "time"],
        temperature[outliers],
        color="red",
        s=18,
        label="LOF anomalies",
        zorder=3
    )

    ax.set(
        title=f"Temperature Anomaly Detection – {region} (2024)",
        xlabel="Date",
        ylabel="Average temperature (°C)"
    )

    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()

    # Summary statistics
    summary = {
        "n_observations": len(data),
        "mean_temperature": float(np.mean(temperature)),
        "min_temperature": float(np.min(temperature)),
        "max_temperature": float(np.max(temperature)),
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
    Perform STL decomposition on reservoir filling degree.

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

    # Plot decomposition
    fig = result.plot()
    fig.set_size_inches(14, 9)

    fig.suptitle(
        "STL Decomposition of Reservoir Filling Degree",
        fontsize=14,
        y=1.02
    )

    plt.tight_layout()

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
    Plot a spectrogram of weekly reservoir filling degree.

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
    dates = pd.to_datetime(data[date_col]).reset_index(drop=True)

    time_indices = np.clip(
        np.round(times).astype(int),
        0,
        len(dates) - 1
    )

    spectrogram_dates = dates.iloc[time_indices]

    # Plot spectrogram
    fig, ax = plt.subplots(figsize=(14, 6))

    mesh = ax.pcolormesh(
        spectrogram_dates,
        frequencies,
        10 * np.log10(power + 1e-12),
        shading="auto",
        cmap="viridis"
    )

    # Mark the annual frequency
    ax.axhline(
        1 / 52,
        color="red",
        linestyle="--",
        label="Annual cycle (52 weeks)"
    )

    ax.set(
        title="Spectrogram of Reservoir Filling Degree – NO3",
        xlabel="Year",
        ylabel="Frequency (cycles/week)"
    )

    ax.legend()

    fig.colorbar(
        mesh,
        ax=ax,
        label="Power (dB)"
    )

    plt.tight_layout()

    summary = {
        "n_observations": len(values),
        "window_length": window_length,
        "overlap": overlap,
        "n_time_windows": len(times),
        "n_frequencies": len(frequencies)
    }

    return fig, summary
