
import os
import pandas as pd

from dotenv import load_dotenv
from entsoe import EntsoePandasClient


# 1. Load API token
load_dotenv()

client = EntsoePandasClient(
    api_key=os.getenv("ENTSOE_API_TOKEN")
)

# 2. Select period
start = pd.Timestamp("2024-04-01", tz="Europe/Oslo")
end = pd.Timestamp("2024-05-01", tz="Europe/Oslo")

# 3. Define import and export directions
flows = {
    "Import": ("FI", "NO_4"),
    "Export": ("NO_4", "FI"),
}

# 4. Check each direction separately
for direction, (source, destination) in flows.items():

    print(f"\n=== {direction.upper()} ===")

    series = client.query_crossborder_flows(
        source,
        destination,
        start=start,
        end=end
    ).sort_index()

    # Check number of observations
    print("Observations:", len(series))

    # Check missing values
    print("Missing values:", series.isna().sum())

    # Calculate time differences
    intervals = (
        series.index.to_series()
        .diff()
        .dropna()
    )

    # Display interval distribution
    print("\nInterval distribution:")
    print(intervals.value_counts())

    # Identify changes in interval duration
    changes = intervals[
        intervals.ne(intervals.shift())
    ]

    print("\nInterval changes:")
    print(changes)

    # Check first and last timestamps
    print("\nTime coverage:")
    print("First:", series.index.min())
    print("Last:", series.index.max())
