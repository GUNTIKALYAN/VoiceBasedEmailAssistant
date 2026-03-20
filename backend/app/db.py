from pymongo import MongoClient

MONGO_URL = "mongodb://mongo:27017"

client = MongoClient(MONGO_URL)
db = client["Voice_Email"]

user_auth_collection = db["user_auth"]

user_auth_collection.create_index("email", unique=True)
