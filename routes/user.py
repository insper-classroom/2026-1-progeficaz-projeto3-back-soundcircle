from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import get_user_by_id, update_display_name, get_user_by_display_name
from models.rating import get_rated_tracks_by_user
from models.feed import get_tracks_by_ids
from utils.helpers import sanitize_text

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


# ───────────────────────────────────────────────────────────────
# Profile
# ───────────────────────────────────────────────────────────────

@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado."}), 404
    return jsonify({
        "id": user["_id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "created_at": user.get("created_at"),
    }), 200


def _update_profile(user_id, new_name):
    if not new_name:
        return jsonify({"error": "Nome de exibição é obrigatório."}), 400

    existing = get_user_by_display_name(new_name)
    if existing and existing["_id"] != user_id:
        return jsonify({"error": "Nome de exibição já está em uso."}), 409

    user = update_display_name(user_id, new_name)
    return jsonify({
        "id": user["_id"],
        "email": user["email"],
        "display_name": user["display_name"],
    }), 200


# Legacy alias
@user_bp.route("/display-name", methods=["PUT"])
@jwt_required()
def change_display_name():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    new_name = sanitize_text(data.get("display_name", ""))
    return _update_profile(user_id, new_name)


# RESTful: PATCH /api/user/profile
@user_bp.route("/profile", methods=["PATCH"])
@jwt_required()
def patch_profile():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    new_name = sanitize_text(data.get("display_name", ""))
    return _update_profile(user_id, new_name)


# ───────────────────────────────────────────────────────────────
# Rated tracks
# ───────────────────────────────────────────────────────────────

@user_bp.route("/rated-tracks", methods=["GET"])
@jwt_required()
def rated_tracks():
    user_id = get_jwt_identity()
    ratings = get_rated_tracks_by_user(user_id)
    track_ids = [r["track_id"] for r in ratings]
    tracks = {t["spotify_id"]: t for t in get_tracks_by_ids(track_ids)}

    result = []
    for r in ratings:
        track = tracks.get(r["track_id"], {})
        sentiment = track.get("sentiment_adjustment", 0.0)
        avg_rating = track.get("average_rating", 0.0)
        rating_count = track.get("rating_count", 0)
        result.append({
            "track_id": r["track_id"],
            "track_name": track.get("name", ""),
            "artist": track.get("artist", ""),
            "album": track.get("album", ""),
            "cover_url": track.get("cover_url", ""),
            "score": r["score"],
            "sentiment_adjustment": sentiment,
            "average_rating": avg_rating,
            "rating_count": rating_count,
            "created_at": r.get("created_at"),
        })

    return jsonify({"ratings": result}), 200
