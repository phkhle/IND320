import os
import pandas as pd

from dotenv import load_dotenv
from pymongo import MongoClient


def get_entsoe_monthly_data():
    """
    Get monthly ENTSO-E-testdata from MongoDB Atlas.
    """

    load_dotenv()

    uri = os.getenv("MONGODB_URI")

    if not uri:
        raise ValueError("MONGODB_URI is missing in .env")

    client = MongoClient(uri, serverSelectionTimeoutMS=10000)

    try:
        db = client["IND320"]
        collection = db["entsoe_monthly_test"]

        documents = list(
            collection.find(
                {"is_test_data": True},
                {"_id": 0}
            )
        )

        df = pd.DataFrame(documents)

        return df

    finally:
        client.close()

# Set main block to run the function and print the DataFrame
if __name__ == "__main__":
    df = get_entsoe_monthly_data()

    print(df)
    print("Number of rows:", len(df))