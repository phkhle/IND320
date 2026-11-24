import numpy as np
import pandas as pd

from river import compose, preprocessing, linear_model, time_series

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from itertools import product


def forecast_reservoir(
    df,
    n_lags=4,
    test_weeks=52
):
    """
    One-week-ahead reservoir filling forecast using River.

    Uses previous reservoir filling values as lag features.
    """

    data = df.sort_values("dato_Id").copy()

    # Use reservoir filling degree
    data["fyllingsgrad"] = pd.to_numeric(
        data["fyllingsgrad"],
        errors="coerce"
    )

    # Create lag features
    for lag in range(1, n_lags + 1):
        data[f"lag_{lag}"] = data["fyllingsgrad"].shift(lag)

    data = data.dropna(
        subset=["fyllingsgrad"] +
        [f"lag_{lag}" for lag in range(1, n_lags + 1)]
    ).reset_index(drop=True)

    if len(data) <= test_weeks:
        raise ValueError(
            "Not enough observations for the selected test period."
        )

    # River pipeline
    model = compose.Pipeline(
        preprocessing.StandardScaler(),
        linear_model.LinearRegression()
    )

    # Split chronologically
    train = data.iloc[:-test_weeks]
    test = data.iloc[-test_weeks:]

    feature_cols = [
        f"lag_{lag}" for lag in range(1, n_lags + 1)
    ]

    # Initial training
    for _, row in train.iterrows():

        x = {
            col: float(row[col])
            for col in feature_cols
        }

        y = float(row["fyllingsgrad"])

        model.learn_one(x, y)

    # Test: predict first, then update model
    results = []

    for _, row in test.iterrows():

        x = {
            col: float(row[col])
            for col in feature_cols
        }

        y_true = float(row["fyllingsgrad"])

        y_pred = model.predict_one(x)

        results.append({
            "date": row["dato_Id"],
            "actual": y_true,
            "predicted": float(y_pred)
        })

        # Update only after the observation becomes available
        model.learn_one(x, y_true)

    return pd.DataFrame(results)


def forecast_reservoir_multistep(
    df,
    n_lags=4,
    horizon=12
):
    """
    Train a River model on historical reservoir filling
    and recursively forecast the next `horizon` weeks.

    No future observed filling values are used.
    """

    import pandas as pd
    from river import compose, preprocessing, linear_model

    data = df.sort_values("dato_Id").copy()

    data["dato_Id"] = pd.to_datetime(data["dato_Id"])
    data["fyllingsgrad"] = pd.to_numeric(
        data["fyllingsgrad"],
        errors="coerce"
    )

    # Prepare weekly observations
    data = (
        data.dropna(subset=["dato_Id", "fyllingsgrad"])
        .drop_duplicates(subset=["dato_Id"])
        .set_index("dato_Id")
        .sort_index()
    )

    # Preserve missing weeks rather than treating them
    # as consecutive observations.
    data = data["fyllingsgrad"].asfreq("7D")

    lag_cols = [f"lag_{i}" for i in range(1, n_lags + 1)]

    training = pd.DataFrame({"fyllingsgrad": data})

    for lag in range(1, n_lags + 1):
        training[f"lag_{lag}"] = data.shift(lag)

    training = training.dropna()

    if training.empty or data.iloc[-n_lags:].isna().any():
        raise ValueError(
            "Not enough consecutive weekly observations."
        )

    model = compose.Pipeline(
        preprocessing.StandardScaler(),
        linear_model.LinearRegression()
    )

    # Train chronologically
    for _, row in training.iterrows():
        x = {col: float(row[col]) for col in lag_cols}
        y = float(row["fyllingsgrad"])

        model.learn_one(x, y)

    # Most recent observations
    history = data.iloc[-n_lags:].tolist()

    predictions = []

    for step in range(1, horizon + 1):

        x = {
            f"lag_{lag}": float(history[-lag])
            for lag in range(1, n_lags + 1)
        }

        y_pred = float(model.predict_one(x))

        predictions.append(y_pred)

        # Feed prediction back as input
        history.append(y_pred)

    forecast_dates = pd.date_range(
        start=data.index[-1] + pd.Timedelta(weeks=1),
        periods=horizon,
        freq="7D"
    )

    return pd.DataFrame({
        "date": forecast_dates,
        "predicted": predictions
    })

def forecast_reservoir_snarimax(
    df,
    horizon=12,
    p=1,
    d=1,
    q=1,
    m=52,
    sp=1,
    sd=0,
    sq=0
):
    """
    Train SNARIMAX on historical weekly reservoir filling
    and forecast multiple weeks ahead.
    """

    data = df.copy()

    data["dato_Id"] = pd.to_datetime(data["dato_Id"])
    data["fyllingsgrad"] = pd.to_numeric(
        data["fyllingsgrad"], errors="coerce"
    )

    series = (
        data.dropna(subset=["dato_Id"])
        .sort_values("dato_Id")
        .drop_duplicates("dato_Id")
        .set_index("dato_Id")["fyllingsgrad"]
        .asfreq("7D")
    )

    # SNARIMAX requires regularly spaced observations.
    # Do not silently replace missing weeks with zero.
    if series.isna().any():
        raise ValueError(
            "Missing weekly observations. Check the date range."
        )

    if len(series) < max(104, m * max(sp, sd, sq) + 2):
        raise ValueError("Insufficient training history.")

    model = time_series.SNARIMAX(
        p=p,
        d=d,
        q=q,
        m=m,
        sp=sp,
        sd=sd,
        sq=sq
    )

    # Train chronologically
    for value in series:
        model.learn_one(float(value))

    # Recursive forecast without future observations
    predictions = model.forecast(horizon=horizon)

    forecast_dates = pd.date_range(
        start=series.index[-1] + pd.Timedelta(weeks=1),
        periods=horizon,
        freq="7D"
    )

    return pd.DataFrame({
        "date": forecast_dates,
        "predicted": predictions
    })



def evaluate_forecasting_models(
    df,
    horizon=12,
    test_weeks=52,
    n_lags=4,
    snarimax_params=None
):
    """
    Rolling-origin evaluation of:
        1. River lag regression
        2. River SNARIMAX
        3. Last-value baseline

    Models are trained only on observations available
    at each forecast origin.
    """

    if snarimax_params is None:
        snarimax_params = {
            "p": 1,
            "d": 1,
            "q": 1,
            "m": 52,
            "sp": 1,
            "sd": 0,
            "sq": 0
        }

    data = df.copy()

    data["dato_Id"] = pd.to_datetime(data["dato_Id"])
    data["fyllingsgrad"] = pd.to_numeric(
        data["fyllingsgrad"],
        errors="coerce"
    )

    data = (
        data.dropna(subset=["dato_Id"])
        .sort_values("dato_Id")
        .drop_duplicates("dato_Id")
        .set_index("dato_Id")["fyllingsgrad"]
        .asfreq("7D")
    )

    # Test origins: last 52 weeks, allowing full horizon
    first_origin = len(data) - test_weeks - 1
    last_origin = len(data) - horizon - 1

    if first_origin < max(104, n_lags):
        raise ValueError("Not enough historical observations.")

    results = []

    for origin in range(first_origin, last_origin + 1):

        history = data.iloc[:origin + 1]

        # Skip origins with missing observations
        if history.isna().any():
            continue

        history_df = history.rename_axis(
            "dato_Id"
        ).reset_index(name="fyllingsgrad")

        river_forecast = forecast_reservoir_multistep(
            df=history_df,
            n_lags=n_lags,
            horizon=horizon
        )

        snarimax_forecast = forecast_reservoir_snarimax(
            df=history_df,
            horizon=horizon,
            **snarimax_params
        )

        future_dates = pd.DatetimeIndex(
            river_forecast["date"]
        )

        actual = data.reindex(future_dates).to_numpy()

        baseline = float(history.iloc[-1])

        for step in range(horizon):

            if np.isnan(actual[step]):
                continue

            for model_name, prediction in [
                ("River", river_forecast["predicted"].iloc[step]),
                ("SNARIMAX", snarimax_forecast["predicted"].iloc[step]),
                ("Baseline", baseline)
            ]:

                results.append({
                    "origin": history.index[-1],
                    "date": future_dates[step],
                    "horizon": step + 1,
                    "model": model_name,
                    "actual": float(actual[step]),
                    "predicted": float(prediction)
                })

    predictions_df = pd.DataFrame(results)

    if predictions_df.empty:
        raise ValueError("No valid forecasts available.")

    metrics = []

    for (model_name, step), group in predictions_df.groupby(
        ["model", "horizon"]
    ):

        y_true = group["actual"]
        y_pred = group["predicted"]

        metrics.append({
            "Model": model_name,
            "Horizon": step,
            "MAE (pp)": mean_absolute_error(
                y_true, y_pred
            ) * 100,
            "RMSE (pp)": np.sqrt(
                mean_squared_error(y_true, y_pred)
            ) * 100,
            "R²": (
                r2_score(y_true, y_pred)
                if len(group) >= 2 else np.nan
            )
        })

    metrics_df = pd.DataFrame(metrics).sort_values(
        ["Horizon", "Model"]
    ).reset_index(drop=True)

    return predictions_df, metrics_df



def tune_snarimax(
    df,
    param_grid=None,
    horizon=12,
    val_weeks=52,
    origin_step=4
):
    """
    Tune SNARIMAX using rolling-origin validation.

    All forecasts use only historical observations
    available at their respective origins.
    """

    if param_grid is None:
        param_grid = {
            "p": [1, 2],
            "d": [1],
            "q": [1, 2],
            "m": [52],
            "sp": [1, 2],
            "sd": [0],
            "sq": [0]
        }

    data = df.copy()

    data["dato_Id"] = pd.to_datetime(data["dato_Id"])
    data["fyllingsgrad"] = pd.to_numeric(
        data["fyllingsgrad"], errors="coerce"
    )

    data = (
        data.dropna(subset=["dato_Id"])
        .sort_values("dato_Id")
        .drop_duplicates("dato_Id")
        .set_index("dato_Id")["fyllingsgrad"]
        .asfreq("7D")
    )

    if horizon < 1 or origin_step < 1:
        raise ValueError("horizon and origin_step must be positive.")

    # Use a validation period before the final test period.
    # The last 52 weeks are reserved for testing.
    test_weeks = 52

    val_end = len(data) - test_weeks - 1
    val_start = val_end - val_weeks + 1

    first_origin = val_start - 1
    last_origin = val_end - horizon

    if first_origin < 104 or last_origin < first_origin:
        raise ValueError("Not enough history for validation.")

    keys = list(param_grid)
    combinations = list(product(*(param_grid[k] for k in keys)))

    results = []

    for i, values in enumerate(combinations, start=1):

        params = dict(zip(keys, values))

        actual_all = []
        predicted_all = []

        for origin in range(
            first_origin,
            last_origin + 1,
            origin_step
        ):

            history = data.iloc[:origin + 1]

            if history.isna().any():
                continue

            history_df = history.rename_axis(
                "dato_Id"
            ).reset_index(name="fyllingsgrad")

            try:
                forecast = forecast_reservoir_snarimax(
                    df=history_df,
                    horizon=horizon,
                    **params
                )
            except (ValueError, ArithmeticError, OverflowError):
                continue

            actual = data.reindex(
                pd.DatetimeIndex(forecast["date"])
            ).to_numpy(dtype=float)

            predicted = forecast["predicted"].to_numpy(
                dtype=float
            )

            valid = np.isfinite(actual) & np.isfinite(predicted)

            # Only score complete forecast horizons
            if valid.sum() != horizon:
                continue

            actual_all.extend(actual)
            predicted_all.extend(predicted)

        if not actual_all:
            continue

        y_true = np.asarray(actual_all)
        y_pred = np.asarray(predicted_all)

        results.append({
            **params,
            "MAE (pp)": mean_absolute_error(y_true, y_pred) * 100,
            "RMSE (pp)": np.sqrt(
                mean_squared_error(y_true, y_pred)
            ) * 100,
            "R²": r2_score(y_true, y_pred),
            "N predictions": len(y_true)
        })

        print(f"{i}/{len(combinations)} completed")

    if not results:
        raise ValueError("No valid parameter configurations.")

    results_df = (
        pd.DataFrame(results)
        .sort_values("RMSE (pp)")
        .reset_index(drop=True)
    )

    best_params = {
        key: int(results_df.iloc[0][key])
        for key in keys
    }

    return results_df, best_params



def evaluate_multistep_forecast(
    df,
    n_lags=4,
    horizon=12,
    test_weeks=52
):
    """
    Evaluate recursive multi-step forecasts using
    historical rolling forecast origins.

    Each forecast uses only observations available
    at its forecast origin.
    """

    data = df.copy()

    data["dato_Id"] = pd.to_datetime(data["dato_Id"])

    data["fyllingsgrad"] = pd.to_numeric(
        data["fyllingsgrad"],
        errors="coerce"
    )

    data = (
        data.dropna(subset=["dato_Id"])
        .sort_values("dato_Id")
        .drop_duplicates("dato_Id")
        .set_index("dato_Id")["fyllingsgrad"]
        .asfreq("7D")
    )

    if len(data) < test_weeks + n_lags + horizon:
        raise ValueError("Not enough historical data.")

    results = []

    # Rolling forecast origins in the test period
    for origin in range(
        len(data) - test_weeks - 1,
        len(data) - horizon
    ):

        history = data.iloc[:origin + 1]

        # Require complete recent lag observations
        if history.iloc[-n_lags:].isna().any():
            continue

        forecast = forecast_reservoir_multistep(
            df=history.reset_index(),
            n_lags=n_lags,
            horizon=horizon
        )

        actual = data.reindex(
            pd.DatetimeIndex(forecast["date"])
        ).to_numpy()

        for step, (date, y_true, y_pred) in enumerate(
            zip(
                forecast["date"],
                actual,
                forecast["predicted"]
            ),
            start=1
        ):

            if pd.isna(y_true):
                continue

            results.append({
                "origin": history.index[-1],
                "date": date,
                "horizon": step,
                "actual": float(y_true),
                "predicted": float(y_pred),
                "baseline": float(history.iloc[-1])
            })

    predictions = pd.DataFrame(results)

    if predictions.empty:
        raise ValueError("No valid forecasts available.")

    metrics = []

    for step, group in predictions.groupby("horizon"):

        y_true = group["actual"]

        for model_name, pred_col in [
            ("River", "predicted"),
            ("Baseline", "baseline")
        ]:

            y_pred = group[pred_col]

            metrics.append({
                "Horizon": step,
                "Model": model_name,
                "MAE (pp)": mean_absolute_error(
                    y_true, y_pred
                ) * 100,
                "RMSE (pp)": np.sqrt(
                    mean_squared_error(y_true, y_pred)
                ) * 100,
                "R²": r2_score(y_true, y_pred)
                if len(group) >= 2 else np.nan
            })

    metrics_df = pd.DataFrame(metrics)

    return predictions, metrics_df