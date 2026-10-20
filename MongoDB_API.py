
import os
import pandas as pd

from dotenv import load_dotenv
from pymongo import MongoClient


# ============================================================
# 1. GENERAL FUNCTION FOR READING MONGODB DATA
# ============================================================

def get_mongodb_data(collection_name):
    """
    Retrieve real ENTSO-E data from a MongoDB collection.
    """

    load_dotenv()

    uri = os.getenv("MONGODB_URI")

    if not uri:
        import streamlit as st
        uri = st.secrets.get("MONGODB_URI")

   
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000
    )

    try:
        db = client["IND320"]
        collection = db[collection_name]

        documents = list(
            collection.find(
                {"is_test_data": False},
                {"_id": 0}
            )
        )

        return pd.DataFrame(documents)

    finally:
        client.close()


# ============================================================
# 2. RETRIEVE MONTHLY ENTSO-E DATA
# ============================================================

def get_entsoe_monthly_data():
    """
    Retrieve monthly electricity import and export data.
    """

    return get_mongodb_data("entsoe_monthly")


# ============================================================
# 3. RETRIEVE DAILY ENTSO-E DATA
# ============================================================

def get_entsoe_daily_data():
    """
    Retrieve daily electricity import and export data.
    """

    return get_mongodb_data("entsoe_daily")


# ============================================================
# 4. TEST FUNCTIONS
# ============================================================

if __name__ == "__main__":

    # Test monthly data
    df_monthly = get_entsoe_monthly_data()

    print("\n=== MONTHLY DATA ===")
    print(df_monthly.head())
    print("Number of rows:", len(df_monthly))

    # Test daily data
    df_daily = get_entsoe_daily_data()

    print("\n=== DAILY DATA ===")
    print(df_daily.head())
    print("Number of rows:", len(df_daily))

    if not df_daily.empty:
        print(
            "Connections:",
            df_daily["connection"].nunique()
        )
        print(
            "Dates:",
            df_daily["date"].nunique()
        )
