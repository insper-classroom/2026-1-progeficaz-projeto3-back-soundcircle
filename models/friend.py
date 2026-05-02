from datetime import datetime, timezone
from models.user import db

friend_requests_collection = db.friend_requests


def send_friend_request(from_user_id, to_user_id):
    now = datetime.now(timezone.utc)
    friend_requests_collection.update_one(
        {"from_user_id": from_user_id, "to_user_id": to_user_id},
        {
            "$set": {
                "from_user_id": from_user_id,
                "to_user_id": to_user_id,
                "status": "pending",
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )


def get_pending_requests(to_user_id):
    return list(
        friend_requests_collection.find(
            {"to_user_id": to_user_id, "status": "pending"}
        ).sort("created_at", -1)
    )


def get_friends(user_id):
    """Retorna lista de IDs de amigos aceitos (em ambas as direções)."""
    accepted = list(
        friend_requests_collection.find(
            {
                "$or": [
                    {"from_user_id": user_id, "status": "accepted"},
                    {"to_user_id": user_id, "status": "accepted"},
                ]
            }
        )
    )
    friends = []
    for req in accepted:
        if req["from_user_id"] == user_id:
            friends.append(req["to_user_id"])
        else:
            friends.append(req["from_user_id"])
    return friends


def respond_to_request(request_id, action):
    from bson.objectid import ObjectId
    status = "accepted" if action == "accept" else "rejected"
    friend_requests_collection.update_one(
        {"_id": ObjectId(request_id)},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
    )


def find_request_by_id(request_id):
    from bson.objectid import ObjectId
    return friend_requests_collection.find_one({"_id": ObjectId(request_id)})


def remove_friendship(user_a, user_b):
    """Remove uma amizade aceita entre dois usuários."""
    result = friend_requests_collection.delete_one(
        {
            "$or": [
                {"from_user_id": user_a, "to_user_id": user_b, "status": "accepted"},
                {"from_user_id": user_b, "to_user_id": user_a, "status": "accepted"},
            ]
        }
    )
    return result.deleted_count > 0


def get_friend_request_between(user_a, user_b):
    return friend_requests_collection.find_one(
        {
            "$or": [
                {"from_user_id": user_a, "to_user_id": user_b},
                {"from_user_id": user_b, "to_user_id": user_a},
            ]
        }
    )
