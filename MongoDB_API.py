import os
import pandas as pd

from dotenv import load_dotenv
from pymongo import MongoClient


def get_entsoe_monthly_data():
    """
    Retrieve real monthly ENTSO-E electricity transfer data
    from MongoDB Atlas.
    """

    load_dotenv()

    uri = os.getenv("MONGODB_URI")

    if not uri:
        raise ValueError("MONGODB_URI is missing in .env")

    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000
    )

    try:
        db = client["IND320"]
        collection = db["entsoe_monthly"]

        documents = list(
            collection.find(
                {"is_test_data": False},
                {"_id": 0}
            )
        )

        return pd.DataFrame(documents)

    finally:
        client.close()


if __name__ == "__main__":
    df = get_entsoe_monthly_data()

    print(df.head())
    print("Number of rows:", len(df))
    print("Connections:", df["connection"].nunique())
    print("Months:", df["month"].nunique())

    # Check missing values
print("\nMissing values:")
print(df.isna().sum())

# Check negative electricity values
print("\nNegative import values:")
print((df["total_import_mwh"] < 0).sum())

print("\nNegative export values:")
print((df["total_export_mwh"] < 0).sum())

# Check number of months per connection
print("\nMonths per connection:")
print(df.groupby("connection")["month"].nunique())

# Check duplicate connection-month combinations
duplicates = df.duplicated(
    subset=["connection", "month"],
    keep=False
)

print("\nDuplicate connection-month combinations:")
print(duplicates.sum())

if duplicates.any():
    print(df[duplicates].sort_values(["connection", "month"]))
else:
    print("No duplicates found.")