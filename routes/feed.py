from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone, timedelta
from models.feed import (
    get_feed_for_date,
    get_feeds_for_date_range,
    save_daily_feed,
    get_tracks_by_ids,
    get_random_tracks_from_pool,
    get_all_tracks_from_pool,
    add_tracks_to_pool,
    acquire_fetch_lock,
    count_pool_tracks,
    update_track_sentiment,
    update_track_average,
)
from models.rating import (
    rate_track,
    get_average_rating,
    get_user_rating,
    get_average_ratings_for_tracks,
    delete_user_rating,
)
from models.comment import add_comment, get_comments_by_track, delete_comment
from models.user import get_user_by_id
from models.promotion import create_promotion, get_active_promotions
from services.rapidapi_spotify import fetch_top_tracks, get_mock_tracks
from services.groq_sentiment import analyze_sentiment
from utils.helpers import sanitize_text

feed_bp = Blueprint("feed", __name__, url_prefix="/api/feed")


def get_today_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _enrich_tracks(tracks, user_id):
    """Adiciona dados do usuário logado (sua nota) em cada track."""
    for t in tracks:
        t.pop("_id", None)
        user_rating = get_user_rating(user_id, t["spotify_id"])
        t["user_score"] = user_rating["score"] if user_rating else None
    return tracks


def _inject_promoted_tracks(tracks):
    """
    Busca promoções ativas, enriquece com dados da track e coloca no topo da lista.
    Adiciona flags is_promoted e promotion_label nas tracks promovidas.
    """
    promoted = get_active_promotions()
    if not promoted:
        return tracks

    promoted_track_ids = [p["track_id"] for p in promoted]
    promoted_tracks_data = get_tracks_by_ids(promoted_track_ids)

    # Mapeia spotify_id -> track_data
    track_map = {t["spotify_id"]: t for t in promoted_tracks_data}

    # Remove do resto do feed para evitar duplicata
    remaining = [t for t in tracks if t["spotify_id"] not in track_map]

    # Prepara tracks promovidas com flags
    result = []
    for p in promoted:
        track_data = track_map.get(p["track_id"])
        if track_data:
            track_data = dict(track_data)
            track_data.pop("_id", None)
            track_data["is_promoted"] = True
            track_data["promotion_label"] = "Anúncio"
            result.append(track_data)

    # Promovidas primeiro, depois o resto
    return result + remaining


def _sort_tracks(tracks, sort_mode):
    """Ordena tracks conforme o filtro selecionado."""
    track_ids = [t["spotify_id"] for t in tracks]

    if sort_mode == "best":
        averages = get_average_ratings_for_tracks(track_ids, days=None)
        for t in tracks:
            t["sort_score"] = averages.get(t["spotify_id"], {}).get("average", 0)
        return sorted(tracks, key=lambda x: x["sort_score"], reverse=True)

    if sort_mode == "worst":
        averages = get_average_ratings_for_tracks(track_ids, days=None)
        for t in tracks:
            t["sort_score"] = averages.get(t["spotify_id"], {}).get("average", 0)
        return sorted(tracks, key=lambda x: x["sort_score"])

    if sort_mode == "trending_day":
        averages = get_average_ratings_for_tracks(track_ids, days=1)
        for t in tracks:
            t["sort_score"] = averages.get(t["spotify_id"], {}).get("average", 0)
        return sorted(tracks, key=lambda x: x["sort_score"], reverse=True)

    if sort_mode == "trending_3days":
        averages = get_average_ratings_for_tracks(track_ids, days=3)
        for t in tracks:
            t["sort_score"] = averages.get(t["spotify_id"], {}).get("average", 0)
        return sorted(tracks, key=lambda x: x["sort_score"], reverse=True)

    if sort_mode == "trending_7days":
        averages = get_average_ratings_for_tracks(track_ids, days=7)
        for t in tracks:
            t["sort_score"] = averages.get(t["spotify_id"], {}).get("average", 0)
        return sorted(tracks, key=lambda x: x["sort_score"], reverse=True)

    # default: ordem original
    return tracks


# ───────────────────────────────────────────────────────────────
# Feed (Daily / Weekly / Monthly)
# ───────────────────────────────────────────────────────────────

@feed_bp.route("/daily", methods=["GET"])
@jwt_required()
def daily_feed():
    user_id = get_jwt_identity()
    today = get_today_str()
    sort_mode = request.args.get("sort", "")
    period = request.args.get("period", "daily")

    # ── PERÍODO: DAILY ──
    if period == "daily":
        feed_state = get_feed_for_date(today)
        if feed_state:
            tracks = get_tracks_by_ids(feed_state.get("track_ids", []))
            tracks = _enrich_tracks(tracks, user_id)
            tracks = _sort_tracks(tracks, sort_mode)
            tracks = _inject_promoted_tracks(tracks)
            return jsonify({
                "date": today,
                "source": "cache",
                "period": "daily",
                "tracks": tracks,
            }), 200

        # ── PRIMEIRO USUÁRIO DO DIA ──
        # Só chama RapidAPI se conseguir o lock (1 vez por dia, atômico)
        if acquire_fetch_lock():
            print("[RapidAPI] Lock adquirido. Buscando 20 músicas...")
            new_tracks = fetch_top_tracks(limit=20)
            if new_tracks:
                add_tracks_to_pool(new_tracks)
                print(f"[RapidAPI] {len(new_tracks)} músicas adicionadas ao pool.")
            else:
                print("[RapidAPI] Fetch falhou ou retornou vazio.")
        else:
            print("[RapidAPI] Lock já existe hoje. Pulando fetch.")

        # Sorteia 20 músicas do pool para o feed do dia
        tracks = get_random_tracks_from_pool(limit=20, exclude_seeds=True)
        source = "mongodb_pool"

        if not tracks:
            tracks = get_mock_tracks()
            source = "seed"

        save_daily_feed(today, tracks)
        tracks = _enrich_tracks(tracks, user_id)
        tracks = _sort_tracks(tracks, sort_mode)
        tracks = _inject_promoted_tracks(tracks)

        return jsonify({
            "date": today,
            "source": source,
            "period": "daily",
            "tracks": tracks,
        }), 200

    # ── PERÍODO: WEEKLY ──
    # Mostra TODAS as músicas do pool acumulado
    if period == "weekly":
        tracks = get_all_tracks_from_pool(exclude_seeds=True)
        tracks = _enrich_tracks(tracks, user_id)
        tracks = _sort_tracks(tracks, sort_mode)
        tracks = _inject_promoted_tracks(tracks)
        return jsonify({
            "date": today,
            "source": "full_pool",
            "period": "weekly",
            "tracks": tracks,
        }), 200

    # ── PERÍODO: MONTHLY ──
    # Mostra TODAS as músicas do pool acumulado
    if period == "monthly":
        tracks = get_all_tracks_from_pool(exclude_seeds=True)
        tracks = _enrich_tracks(tracks, user_id)
        tracks = _sort_tracks(tracks, sort_mode)
        tracks = _inject_promoted_tracks(tracks)
        return jsonify({
            "date": today,
            "source": "full_pool",
            "period": "monthly",
            "tracks": tracks,
        }), 200

    # Parâmetro period inválido
    return jsonify({"error": "period deve ser daily, weekly ou monthly."}), 400


# ───────────────────────────────────────────────────────────────
# Ratings
# ───────────────────────────────────────────────────────────────

def _create_or_update_rating(user_id, track_id, score):
    """Lógica compartilhada para criar/atualizar uma avaliação."""
    if not track_id or score is None:
        return jsonify({"error": "track_id e score são obrigatórios."}), 400

    try:
        score = float(score)
        if score < 1.0 or score > 5.0:
            return jsonify({"error": "A nota deve estar entre 1.0 e 5.0."}), 422
    except ValueError:
        return jsonify({"error": "Nota inválida."}), 422

    rate_track(user_id, track_id, score)

    # Recalcula média
    avg = get_average_rating(track_id)
    update_track_average(track_id, avg["average"], avg["count"])

    return jsonify({
        "message": "Avaliação salva.",
        "track_id": track_id,
        "score": round(score, 1),
        "average_rating": avg["average"],
        "rating_count": avg["count"],
    }), 200


# Legacy alias
@feed_bp.route("/rate", methods=["POST"])
@jwt_required()
def rate():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    return _create_or_update_rating(user_id, data.get("track_id", ""), data.get("score"))


# RESTful: POST /api/feed/tracks/<track_id>/ratings
@feed_bp.route("/tracks/<track_id>/ratings", methods=["POST"])
@jwt_required()
def create_rating(track_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    score = data.get("score")
    return _create_or_update_rating(user_id, track_id, score)


# RESTful: DELETE /api/feed/tracks/<track_id>/ratings
@feed_bp.route("/tracks/<track_id>/ratings", methods=["DELETE"])
@jwt_required()
def remove_rating(track_id):
    user_id = get_jwt_identity()
    deleted = delete_user_rating(user_id, track_id)
    if not deleted:
        return jsonify({"error": "Avaliação não encontrada."}), 404

    # Recalcula média
    avg = get_average_rating(track_id)
    update_track_average(track_id, avg["average"], avg["count"])

    return "", 204


# ───────────────────────────────────────────────────────────────
# Comments
# ───────────────────────────────────────────────────────────────

def _get_comments_for_track(track_id):
    """Lógica compartilhada para listar comentários."""
    comments = get_comments_by_track(track_id)
    for c in comments:
        c["_id"] = str(c["_id"])
    return jsonify({"track_id": track_id, "comments": comments}), 200


def _create_comment(user_id, track_id, text):
    """Lógica compartilhada para criar um comentário."""
    if not track_id or not text:
        return jsonify({"error": "track_id e text são obrigatórios."}), 400

    user = get_user_by_id(user_id)
    display_name = user.get("display_name", user.get("email", "Usuário")) if user else "Usuário"

    comment = add_comment(user_id, display_name, track_id, text)

    # Análise de sentimento: busca todos os comentários da música e reavalia
    all_comments = get_comments_by_track(track_id)
    texts = [c["text"] for c in all_comments]
    sentiment = analyze_sentiment(texts)
    if sentiment is not None:
        update_track_sentiment(track_id, sentiment)

    return jsonify({"message": "Comentário adicionado.", "comment": comment}), 201


# Legacy alias
@feed_bp.route("/comments/<track_id>", methods=["GET"])
@jwt_required()
def get_comments(track_id):
    return _get_comments_for_track(track_id)


# RESTful: GET /api/feed/tracks/<track_id>/comments
@feed_bp.route("/tracks/<track_id>/comments", methods=["GET"])
@jwt_required()
def list_comments(track_id):
    return _get_comments_for_track(track_id)


# Legacy alias
@feed_bp.route("/comment", methods=["POST"])
@jwt_required()
def post_comment():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    track_id = data.get("track_id", "")
    text = sanitize_text(data.get("text", ""))
    return _create_comment(user_id, track_id, text)


# RESTful: POST /api/feed/tracks/<track_id>/comments
@feed_bp.route("/tracks/<track_id>/comments", methods=["POST"])
@jwt_required()
def create_comment(track_id):
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    text = sanitize_text(data.get("text", ""))
    return _create_comment(user_id, track_id, text)


# RESTful: DELETE /api/feed/tracks/<track_id>/comments/<comment_id>
@feed_bp.route("/tracks/<track_id>/comments/<comment_id>", methods=["DELETE"])
@jwt_required()
def remove_comment(track_id, comment_id):
    user_id = get_jwt_identity()
    deleted = delete_comment(comment_id, user_id)
    if not deleted:
        return jsonify({"error": "Comentário não encontrado ou sem permissão."}), 404

    # Reavalia sentimento após remoção
    all_comments = get_comments_by_track(track_id)
    texts = [c["text"] for c in all_comments]
    sentiment = analyze_sentiment(texts)
    if sentiment is not None:
        update_track_sentiment(track_id, sentiment)
    else:
        update_track_sentiment(track_id, 0.0)

    return "", 204


# ───────────────────────────────────────────────────────────────
# Promote Track (Checkout Falso)
# ───────────────────────────────────────────────────────────────

@feed_bp.route("/promote", methods=["POST"])
@jwt_required()
def promote_track():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    track_id = data.get("track_id", "").strip()

    if not track_id:
        return jsonify({"error": "track_id é obrigatório."}), 400

    # Verifica se a música existe no pool
    from models.feed import tracks_collection
    track = tracks_collection.find_one({"spotify_id": track_id})
    if not track:
        return jsonify({"error": "Música não encontrada."}), 404

    # Cria a promoção (checkout falso — qualquer cartão aceito)
    promotion = create_promotion(
        track_id=track_id,
        user_id=user_id,
        amount=25.0,
        currency="USD",
        duration_days=7,
    )

    return jsonify({
        "message": "Música impulsionada com sucesso!",
        "promotion_id": promotion["_id"],
        "track_id": track_id,
        "amount": promotion["amount"],
        "currency": promotion["currency"],
        "expires_at": promotion["expires_at"].isoformat(),
    }), 201


# ───────────────────────────────────────────────────────────────
# Sentiment
# ───────────────────────────────────────────────────────────────

def _get_track_sentiment(track_id):
    from models.feed import tracks_collection
    track = tracks_collection.find_one({"spotify_id": track_id})
    if not track:
        return jsonify({"error": "Música não encontrada."}), 404
    return jsonify({
        "track_id": track_id,
        "sentiment_adjustment": track.get("sentiment_adjustment", 0.0),
    }), 200


# Legacy alias
@feed_bp.route("/sentiment/<track_id>", methods=["GET"])
@jwt_required()
def get_sentiment(track_id):
    return _get_track_sentiment(track_id)


# RESTful: GET /api/feed/tracks/<track_id>/sentiment
@feed_bp.route("/tracks/<track_id>/sentiment", methods=["GET"])
@jwt_required()
def track_sentiment(track_id):
    return _get_track_sentiment(track_id)
