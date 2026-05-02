from datetime import datetime, timezone
from models.user import db

ratings_collection = db.ratings


def rate_track(user_id, track_id, score):
    """Salva ou atualiza a nota de um usuário para uma música."""
    now = datetime.now(timezone.utc)
    ratings_collection.update_one(
        {"user_id": user_id, "track_id": track_id},
        {
            "$set": {
                "user_id": user_id,
                "track_id": track_id,
                "score": round(float(score), 1),
                "updated_at": now,
            },
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )


def get_average_rating(track_id):
    """Calcula a média das notas de uma música."""
    pipeline = [
        {"$match": {"track_id": track_id}},
        {
            "$group": {
                "_id": "$track_id",
                "average": {"$avg": "$score"},
                "count": {"$sum": 1},
            }
        },
    ]
    result = list(ratings_collection.aggregate(pipeline))
    if result:
        return {
            "average": round(result[0]["average"], 1),
            "count": result[0]["count"],
        }
    return {"average": 0.0, "count": 0}


def get_user_rating(user_id, track_id):
    """Busca a nota que um usuário deu para uma música."""
    return ratings_collection.find_one({"user_id": user_id, "track_id": track_id})


def get_rated_tracks_by_user(user_id):
    """Lista todas as avaliações de um usuário."""
    return list(ratings_collection.find({"user_id": user_id}).sort("created_at", -1))


def delete_user_rating(user_id, track_id):
    """Remove a avaliação de um usuário para uma música."""
    result = ratings_collection.delete_one({"user_id": user_id, "track_id": track_id})
    return result.deleted_count > 0


def get_average_ratings_for_tracks(track_ids, days=None):
    """
    Calcula a média das notas para uma lista de tracks.
    Se days=None, calcula média geral.
    Se days=N, calcula apenas avaliações dos últimos N dias.
    Retorna dict: {track_id: {"average": float, "count": int}}
    """
    match_stage = {"track_id": {"$in": track_ids}}
    if days is not None:
        from datetime import timedelta
        since = datetime.now(timezone.utc) - timedelta(days=days)
        match_stage["created_at"] = {"$gte": since}

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": "$track_id",
                "average": {"$avg": "$score"},
                "count": {"$sum": 1},
            }
        },
    ]
    results = list(ratings_collection.aggregate(pipeline))
    output = {}
    for r in results:
        output[r["_id"]] = {
            "average": round(r["average"], 1),
            "count": r["count"],
        }
    return output
