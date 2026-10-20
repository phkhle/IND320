import json
import os

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne


# Load environment variables
load_dotenv()

mongo_uri = os.getenv("MONGODB_URI")

if not mongo_uri:
    raise ValueError("MONGODB_URI is missing from .env")


# Read the exported JSON file
with open("entsoe_monthly.json", "r", encoding="utf-8") as file:
    documents = json.load(file)

if len(documents) != 216:
    raise ValueError(f"Expected 216 documents, found {len(documents)}")


# Connect to MongoDB
client = MongoClient(mongo_uri, serverSelectionTimeoutMS=10000)

try:
    client.admin.command("ping")

    database = client["IND320"]
    collection = database["entsoe_monthly"]

    # Insert or update documents without creating duplicates
    operations = [
        UpdateOne(
            {
                "connection": doc["connection"],
                "month": doc["month"]
            },
            {"$set": doc},
            upsert=True
        )
        for doc in documents
    ]

    result = collection.bulk_write(operations, ordered=False)

    print("MongoDB upload completed.")
    print("Inserted:", result.upserted_count)
    print("Updated:", result.modified_count)
    print("Total documents:", collection.count_documents({}))

finally:
    client.close()