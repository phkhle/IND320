
import os
import json

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne


# ============================================================
# 1. CONNECT TO MONGODB ATLAS
# ============================================================

load_dotenv()

uri = os.getenv("MONGODB_URI")

if not uri:
    raise ValueError("MONGODB_URI is missing from .env")

client = MongoClient(uri, serverSelectionTimeoutMS=10000)

try:
    client.admin.command("ping")
    print("Successfully connected to MongoDB Atlas!")

    db = client["IND320"]
    collection = db["entsoe_daily"]

    # ========================================================
    # 2. LOAD DAILY JSON DATA
    # ========================================================

    with open("entsoe_daily.json", "r", encoding="utf-8") as file:
        documents = json.load(file)

    print(f"Loaded {len(documents)} daily documents.")

    # ========================================================
    # 3. INSERT OR UPDATE DOCUMENTS
    # ========================================================

    operations = [
        UpdateOne(
            {
                "connection": doc["connection"],
                "date": doc["date"]
            },
            {"$set": doc},
            upsert=True
        )
        for doc in documents
    ]

    if operations:
        result = collection.bulk_write(operations, ordered=False)

        print("Inserted:", result.upserted_count)
        print("Updated:", result.modified_count)

    # ========================================================
    # 4. VERIFY DATA
    # ========================================================

    print(
        "Total daily documents in MongoDB:",
        collection.count_documents({})
    )

finally:
    client.close()
