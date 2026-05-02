from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.friend import (
    send_friend_request,
    get_pending_requests,
    get_friends,
    respond_to_request,
    find_request_by_id,
    get_friend_request_between,
    remove_friendship,
)
from models.user import get_user_by_id, get_user_by_display_name
from bson.objectid import ObjectId

friends_bp = Blueprint("friends", __name__, url_prefix="/api/friends")


# ───────────────────────────────────────────────────────────────
# List friends
# ───────────────────────────────────────────────────────────────

@friends_bp.route("", methods=["GET"])
@jwt_required()
def list_friends():
    user_id = get_jwt_identity()
    friend_ids = get_friends(user_id)
    result = []
    for fid in friend_ids:
        user = get_user_by_id(fid)
        if user:
            result.append({
                "id": user["_id"],
                "display_name": user.get("display_name", ""),
                "email": user.get("email", ""),
            })
    return jsonify({"friends": result}), 200


# ───────────────────────────────────────────────────────────────
# Pending requests
# ───────────────────────────────────────────────────────────────

@friends_bp.route("/pending", methods=["GET"])
@jwt_required()
def pending_requests():
    user_id = get_jwt_identity()
    requests = get_pending_requests(user_id)
    result = []
    for req in requests:
        from_user = get_user_by_id(req["from_user_id"])
        result.append({
            "request_id": str(req["_id"]),
            "from_user_id": req["from_user_id"],
            "from_display_name": from_user.get("display_name", "") if from_user else "",
            "status": req["status"],
            "created_at": req.get("created_at"),
        })
    return jsonify({"requests": result}), 200


# ───────────────────────────────────────────────────────────────
# Send friend request
# ───────────────────────────────────────────────────────────────

def _send_request(user_id, display_name):
    if not display_name:
        return jsonify({"error": "Nome de exibição é obrigatório."}), 400

    target = get_user_by_display_name(display_name)
    if not target:
        return jsonify({"error": "Usuário não encontrado."}), 404

    target_id = target["_id"]
    if target_id == user_id:
        return jsonify({"error": "Não pode adicionar a si mesmo."}), 400

    existing = get_friend_request_between(user_id, target_id)
    if existing:
        if existing["status"] == "accepted":
            return jsonify({"error": "Vocês já são amigos."}), 409
        if existing["status"] == "pending":
            return jsonify({"error": "Solicitação já pendente."}), 409

    send_friend_request(user_id, target_id)
    return jsonify({"message": "Solicitação enviada."}), 201


# Legacy alias
@friends_bp.route("/request", methods=["POST"])
@jwt_required()
def request_friend():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    display_name = data.get("display_name", "").strip()
    return _send_request(user_id, display_name)


# RESTful: POST /api/friends
@friends_bp.route("", methods=["POST"])
@jwt_required()
def create_friendship():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    display_name = data.get("display_name", "").strip()
    return _send_request(user_id, display_name)


# ───────────────────────────────────────────────────────────────
# Respond to request (accept/reject)
# ───────────────────────────────────────────────────────────────

def _respond_to_request(user_id, request_id, action):
    if not request_id or action not in ("accept", "reject"):
        return jsonify({"error": "request_id e action (accept/reject) são obrigatórios."}), 400

    req = find_request_by_id(request_id)
    if not req:
        return jsonify({"error": "Solicitação não encontrada."}), 404
    if req["to_user_id"] != user_id:
        return jsonify({"error": "Sem permissão."}), 403

    respond_to_request(request_id, action)
    return "", 204


# Legacy alias
@friends_bp.route("/respond", methods=["PUT"])
@jwt_required()
def respond():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    return _respond_to_request(user_id, data.get("request_id", ""), data.get("action", ""))


# RESTful: PATCH /api/friends/requests/<request_id>
@friends_bp.route("/requests/<request_id>", methods=["PATCH"])
@jwt_required()
def update_request(request_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    action = data.get("action", "").strip()
    return _respond_to_request(user_id, request_id, action)


# ───────────────────────────────────────────────────────────────
# Remove friend
# ───────────────────────────────────────────────────────────────

@friends_bp.route("/<friend_id>", methods=["DELETE"])
@jwt_required()
def remove_friend(friend_id):
    user_id = get_jwt_identity()
    friend_ids = get_friends(user_id)
    if friend_id not in friend_ids:
        return jsonify({"error": "Vocês não são amigos."}), 403

    removed = remove_friendship(user_id, friend_id)
    if not removed:
        return jsonify({"error": "Não foi possível remover a amizade."}), 404

    return "", 204


# ───────────────────────────────────────────────────────────────
# Friend ratings
# ───────────────────────────────────────────────────────────────

@friends_bp.route("/<friend_id>/ratings", methods=["GET"])
@jwt_required()
def friend_ratings(friend_id):
    user_id = get_jwt_identity()
    friend_ids = get_friends(user_id)
    if friend_id not in friend_ids:
        return jsonify({"error": "Vocês não são amigos."}), 403

    from models.rating import get_rated_tracks_by_user
    from models.feed import get_tracks_by_ids

    ratings = get_rated_tracks_by_user(friend_id)
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
            "cover_url": track.get("cover_url", ""),
            "score": r["score"],
            "sentiment_adjustment": sentiment,
            "average_rating": avg_rating,
            "rating_count": rating_count,
            "created_at": r.get("created_at"),
        })

    return jsonify({"ratings": result}), 200
