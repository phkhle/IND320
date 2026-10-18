
from ENTSOE_API import get_entsoe_data

df = get_entsoe_data(
    start_date="2026-10-01",
    end_date="2026-10-03",
    test_mode=True
)

print(df.head())
print("Number of rows:", len(df))
print("Connections:", df["connection"].nunique())
