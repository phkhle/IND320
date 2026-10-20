
import os
import pandas as pd

from dotenv import load_dotenv
from entsoe import EntsoePandasClient


load_dotenv()


# Norwegian bidding zones and neighboring countries
CONNECTIONS = {
    "NO1-SE3": ("NO_1", "SE_3"),
    "NO3-SE2": ("NO_3", "SE_2"),
    "NO4-SE1": ("NO_4", "SE_1"),
    "NO4-SE2": ("NO_4", "SE_2"),
    "NO4-FI": ("NO_4", "FI"),
    "NO2-DK1": ("NO_2", "DK_1"),
    "NO2-NL": ("NO_2", "NL"),
    "NO2-DE-LU": ("NO_2", "DE_LU"),
    "NO2-GB": ("NO_2", "GB"),
}


def get_entsoe_data(start_date, end_date, test_mode=False):
    """
    Retrieve cross-border electricity flows for Norway.
    """

    start = pd.Timestamp(start_date, tz="Europe/Oslo")
    end = pd.Timestamp(end_date, tz="Europe/Oslo")

    if start >= end:
        raise ValueError("start_date must be before end_date")

    # ---------------------------------------------------------
    # 1. Synthetic test data
    # ---------------------------------------------------------
    if test_mode:

        dates = pd.date_range(
            start=start,
            end=end,
            freq="h",
            inclusive="left"
        )

        rows = []

        for connection in CONNECTIONS:
            for i, timestamp in enumerate(dates):
                rows.append({
                    "timestamp": timestamp,
                    "connection": connection,
                    "import_mwh": float(100 + i % 50),
                    "export_mwh": float(200 + i % 70),
                })

        return pd.DataFrame(rows)

    # ---------------------------------------------------------
    # 2. API authentication
    # ---------------------------------------------------------
    token = os.getenv("ENTSOE_API_TOKEN")

    if not token or token == "YOUR_TOKEN_HERE":
        raise ValueError("ENTSO-E API token is missing.")

    client = EntsoePandasClient(api_key=token)

    results = []

    # ---------------------------------------------------------
    # 3. Retrieve import and export data
    # ---------------------------------------------------------
    for connection, (norway, foreign) in CONNECTIONS.items():

        print(f"Fetching {connection}...")

        # Import: foreign country -> Norway
        imports = client.query_crossborder_flows(
            foreign,
            norway,
            start=start,
            end=end
        )

        # Export: Norway -> foreign country
        exports = client.query_crossborder_flows(
            norway,
            foreign,
            start=start,
            end=end
        )

        # -----------------------------------------------------
        # 4. Validate and combine power values (MW)
        # -----------------------------------------------------
        if imports.empty or exports.empty:
            raise ValueError(
                f"Empty import or export series for {connection}"
            )

        connection_df = pd.DataFrame({
            "import_mw": imports,
            "export_mw": exports
        }).sort_index()

        if connection_df.isna().any().any():
            raise ValueError(
                f"Missing import/export values for {connection}"
            )

        if connection_df.index.has_duplicates:
            raise ValueError(
                f"Duplicate timestamps for {connection}"
            )

        # Convert timestamps to UTC
        connection_df.index = connection_df.index.tz_convert("UTC")

        # -----------------------------------------------------
        # 5. Calculate and validate time intervals
        # -----------------------------------------------------
        # Duration until the next observation
        interval_hours = (
            connection_df.index.to_series()
            .diff()
            .shift(-1)
            .dt.total_seconds() / 3600
        )

        # Determine the final interval from the requested end
        interval_hours.iloc[-1] = (
            end.tz_convert("UTC") - connection_df.index[-1]
        ).total_seconds() / 3600

        # Validate intervals
        valid_intervals = [0.25, 0.5, 1.0]

        if not interval_hours.isin(valid_intervals).all():
            raise ValueError(
                f"Unexpected intervals for {connection}: "
                f"{interval_hours[~interval_hours.isin(valid_intervals)].unique()}"
            )

        # Validate time coverage
        if connection_df.index[0] != start.tz_convert("UTC"):
            raise ValueError(
                f"Incomplete start coverage for {connection}"
            )

        # -----------------------------------------------------
        # 6. Convert MW to MWh
        # -----------------------------------------------------
        connection_df["import_mwh"] = (
            connection_df["import_mw"] * interval_hours
        )

        connection_df["export_mwh"] = (
            connection_df["export_mw"] * interval_hours
        )

        # -----------------------------------------------------
        # 7. Prepare output
        # -----------------------------------------------------
        connection_df = (
            connection_df[
                ["import_mwh", "export_mwh"]
            ]
            .reset_index()
            .rename(columns={"index": "timestamp"})
        )

        connection_df["connection"] = connection

        results.append(connection_df)

    # ---------------------------------------------------------
    # 8. Combine all connections
    # ---------------------------------------------------------
    df = pd.concat(results, ignore_index=True)

    return df[
        ["timestamp", "connection", "import_mwh", "export_mwh"]
    ]
