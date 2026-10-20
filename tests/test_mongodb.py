
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load MongoDB connection string
load_dotenv()

uri = os.getenv("MONGODB_URI")

if not uri:
    raise ValueError("MONGODB_URI is missing from .env")

# Connect to MongoDB Atlas
client = MongoClient(uri, serverSelectionTimeoutMS=10000)

# Test connection
client.admin.command("ping")
print("Successfully connected to MongoDB Atlas!")

# Select database and collection
db = client["IND320"]
collection = db["test_data"]

# Insert test document
test_document = {
    "name": "IND320 Project 2",
    "source": "Python",
    "value": 100
}

collection.insert_one(test_document)
print("Test document inserted successfully!")

# Read document from MongoDB
result = collection.find_one(
    {"name": "IND320 Project 2"},
    {"_id": 0}
)

print("Data retrieved from MongoDB:")
print(result)

client.close()
