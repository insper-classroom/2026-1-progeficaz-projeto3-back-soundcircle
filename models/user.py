from datetime import datetime, timezone
from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_DB_STRING)
db = client["soundcircle"]
users_collection = db.users


def get_user_by_id(user_id):
    return users_collection.find_one({"_id": user_id})


def get_user_by_email(email):
    return users_collection.find_one({"email": email.lower().strip()})


def get_user_by_display_name(display_name):
    display_name = display_name.lower().strip()
    # Try the indexed field first (new users)
    user = users_collection.find_one({"display_name_lower": display_name})
    if user:
        return user
    # Fallback: case-insensitive regex on display_name (legacy users created before display_name_lower)
    return users_collection.find_one({"display_name": {"$regex": "^" + display_name + "$", "$options": "i"}})


def create_user(email, password_hash, display_name):
    email = email.lower().strip()
    display_name = display_name.strip()

    user = {
        "_id": email,
        "email": email,
        "password_hash": password_hash,
        "display_name": display_name,
        "display_name_lower": display_name.lower(),
        "created_at": datetime.now(timezone.utc),
    }
    users_collection.insert_one(user)
    return user


def update_display_name(user_id, display_name):
    display_name = display_name.strip()
    users_collection.update_one(
        {"_id": user_id},
        {"$set": {"display_name": display_name, "display_name_lower": display_name.lower()}}
    )
    return users_collection.find_one({"_id": user_id})