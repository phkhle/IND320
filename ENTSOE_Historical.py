
import pandas as pd
from pathlib import Path

from ENTSOE_API import get_entsoe_data

# This file fetch the entire historical ENTSO-E data for Norway in 2 years of monthly chunks and saves them as CSV files in the data/entsoe directory.

START_DATE = "2024-01-01"
END_DATE = "2026-01-01"

OUTPUT_DIR = Path("data/entsoe")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

months = pd.date_range(
    start=START_DATE,
    end=END_DATE,
    freq="MS"
)

for start, end in zip(months[:-1], months[1:]):

    month = start.strftime("%Y-%m")
    output_file = OUTPUT_DIR / f"entsoe_{month}.csv"

    if output_file.exists():
        print(f"Skipping {month}: already downloaded")
        continue

    print(f"\nFetching {month}...")

    df = get_entsoe_data(
        start_date=start.strftime("%Y-%m-%d"),
        end_date=end.strftime("%Y-%m-%d"),
        test_mode=False
    )

    if df.empty:
        raise ValueError(f"No data for {month}")

    if df.duplicated(["connection", "timestamp"]).any():
        raise ValueError(f"Duplicate timestamps in {month}")

    if df[["import_mwh", "export_mwh"]].isna().any().any():
        raise ValueError(f"Missing values in {month}")

    df.to_csv(output_file, index=False)

    print(f"Saved {len(df)} rows to {output_file}")

print("\nHistorical download completed!")
