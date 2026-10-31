import pandas as pd
from pathlib import Path

for file in sorted(Path("data/entsoe").glob("*.csv")):
    df = pd.read_csv(file)

    print(f"\n=== {file.name} ===")
    print("Rows:", len(df))
    print("Connections:", df["connection"].nunique())
    print("Duplicates:", df.duplicated(["connection", "timestamp"]).sum())
    print("Missing values:", df.isna().sum().sum())
    print("\nRows per connection:")
    print(df.groupby("connection").size())

