import numpy as np
import pandas as pd

from river import compose, preprocessing, linear_model


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