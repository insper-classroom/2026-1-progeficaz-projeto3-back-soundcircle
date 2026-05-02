from datetime import datetime, timezone, timedelta
from models.user import db

promotions_collection = db.promoted_tracks


def create_promotion(track_id, user_id, amount=25.0, currency="USD", duration_days=7):
    """Cria uma nova promoção para uma música."""
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=duration_days)
    promotion = {
        "track_id": track_id,
        "user_id": user_id,
        "amount": amount,
        "currency": currency,
        "paid_at": now,
        "expires_at": expires,
        "status": "active",
        "created_at": now,
    }
    result = promotions_collection.insert_one(promotion)
    promotion["_id"] = str(result.inserted_id)
    return promotion


def get_active_promotions():
    """Retorna todas as promoções ativas (não expiradas)."""
    now = datetime.now(timezone.utc)
    return list(
        promotions_collection.find({
            "expires_at": {"$gte": now},
            "status": "active",
        }).sort("paid_at", -1)
    )


def get_active_promotion_for_track(track_id):
    """Retorna a promoção ativa de uma música específica, se houver."""
    now = datetime.now(timezone.utc)
    return promotions_collection.find_one({
        "track_id": track_id,
        "expires_at": {"$gte": now},
        "status": "active",
    })


def get_promotions_by_user(user_id):
    """Retorna todas as promoções de um usuário."""
    return list(
        promotions_collection.find({"user_id": user_id}).sort("paid_at", -1)
    )
