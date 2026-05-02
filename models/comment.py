from datetime import datetime, timezone
from models.user import db

comments_collection = db.comments


def add_comment(user_id, display_name, track_id, text):
    comment = {
        "user_id": user_id,
        "display_name": display_name,
        "track_id": track_id,
        "text": text,
        "created_at": datetime.now(timezone.utc),
    }
    result = comments_collection.insert_one(comment)
    comment["_id"] = str(result.inserted_id)
    return comment


def delete_comment(comment_id, user_id):
    """Remove um comentário se pertencer ao usuário."""
    from bson.objectid import ObjectId
    result = comments_collection.delete_one({"_id": ObjectId(comment_id), "user_id": user_id})
    return result.deleted_count > 0


def get_comments_by_track(track_id):
    return list(
        comments_collection.find({"track_id": track_id}).sort("created_at", -1)
    )