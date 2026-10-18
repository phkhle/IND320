import os
import json

from dotenv import load_dotenv
from pymongo import MongoClient

# 1. Fetch MongoDB-connection from .env
load_dotenv()

uri = os.getenv("MONGODB_URI")

if not uri:
    raise ValueError("MONGODB_URI is missing in .env")

# 2. Read test data from JSON file
with open("entsoe_monthly_test.json", "r") as f:
    documents = json.load(f)

# 3. Connect to MongoDB Atlas
client = MongoClient(uri, serverSelectionTimeoutMS=10000)

client.admin.command("ping")

db = client["IND320"]
collection = db["entsoe_monthly_test"]

# 4. Save the documents
for doc in documents:
    doc["is_test_data"] = True

    # Use replace_one with upsert=True to avoid duplicates
    collection.replace_one(
        {
            "connection": doc["connection"],
            "month": doc["month"]
        },
        doc,
        upsert=True
    )

print("Documents in MongoDB:", collection.count_documents({}))

client.close()