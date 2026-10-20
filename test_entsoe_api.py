from ENTSOE_API import get_entsoe_data

# Retrieve real ENTSO-E data
# Test with one month of data in January 2025
df = get_entsoe_data(
    start_date="2024-04-01",
    end_date="2024-05-01",
    test_mode=False
)

# 1. Dataset overview
print("\nDataset shape:", df.shape)
print("\nRows per connection:")
print(df.groupby("connection").size())

# 2. Data quality
print("\n=== DATA QUALITY CHECK ===")

print(
    "Duplicates:",
    df.duplicated(["connection", "timestamp"]).sum()
)

print("\nMissing values:")
print(df.isna().sum())

print("\nNegative values:")
print((df[["import_mwh", "export_mwh"]] < 0).sum())

# 3. Time intervals
print("\n=== TIME INTERVALS ===")

for connection, group in df.groupby("connection"):
    intervals = (
        group.sort_values("timestamp")["timestamp"]
        .diff()
        .dropna()
    )

    print(f"\n{connection}")
    print(intervals.value_counts())