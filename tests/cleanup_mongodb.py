# One-time cleanup script.
# Removes the deprecated is_test_data field from MongoDB.
# Do not run as part of the regular data pipeline

import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.environ["MONGODB_URI"])

try:
    db = client["IND320"]

    for name in ["entsoe_daily", "entsoe_monthly"]:
        collection = db[name]

        result = collection.update_many(
            {"is_test_data": False},
            {"$unset": {"is_test_data": ""}}
        )

        print(
            f"{name}: {result.modified_count} documents updated"
        )

finally:
    client.close()
