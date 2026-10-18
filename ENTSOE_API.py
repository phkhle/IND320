
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

    Returns a DataFrame with:
    timestamp, connection, import_mwh, export_mwh

    When test_mode=True, synthetic data is generated.
    """

    start = pd.Timestamp(start_date, tz="Europe/Oslo")
    end = pd.Timestamp(end_date, tz="Europe/Oslo")

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

    token = os.getenv("ENTSOE_API_TOKEN")

    if not token or token == "YOUR_TOKEN_HERE":
        raise ValueError(
            "ENTSO-E API token is missing. "
            "Use test_mode=True until your token arrives."
        )

    client = EntsoePandasClient(api_key=token)
    results = []

    for connection, (norway, foreign) in CONNECTIONS.items():
        print(f"Fetching {connection}...")

        # Import: foreign country -> Norway
        imports = client.query_crossborder_flows(
            foreign, norway, start=start, end=end
        )

        # Export: Norway -> foreign country
        exports = client.query_crossborder_flows(
            norway, foreign, start=start, end=end
        )

        connection_df = pd.DataFrame({
            "import_mwh": imports,
            "export_mwh": exports
        })

        connection_df = connection_df.reset_index()
        connection_df = connection_df.rename(
            columns={"index": "timestamp"}
        )

        connection_df["connection"] = connection
        results.append(connection_df)

    return pd.concat(results, ignore_index=True)
