from datetime import datetime, timezone, timedelta
from pymongo import ASCENDING
from models.user import db

tracks_collection = db.daily_tracks
feed_state_collection = db.feed_state
fetch_lock_collection = db.fetch_lock

# Índice para buscar tracks por data
feed_state_collection.create_index(
    [("date", ASCENDING)],
    unique=True,
    name="idx_date_unique"
)

# Índice TTL para limpar locks antigos (7 dias)
fetch_lock_collection.create_index(
    [("created_at", ASCENDING)],
    expireAfterSeconds=7 * 24 * 60 * 60,
    name="idx_lock_ttl"
)


def get_feed_for_date(date_str):
    """Busca o estado do feed para uma data específica (YYYY-MM-DD)."""
    return feed_state_collection.find_one({"date": date_str})


def get_feeds_for_date_range(start_date_str, end_date_str):
    """Busca feeds entre duas datas (inclusive)."""
    return list(
        feed_state_collection.find({
            "date": {"$gte": start_date_str, "$lte": end_date_str}
        }).sort("date", ASCENDING)
    )


def save_daily_feed(date_str, tracks):
    """Salva as músicas do dia no MongoDB."""
    now = datetime.now(timezone.utc)

    # Salva/atualiza o estado do feed
    feed_state_collection.update_one(
        {"date": date_str},
        {
            "$set": {
                "date": date_str,
                "last_fetch": now,
                "track_ids": [t["spotify_id"] for t in tracks],
            }
        },
        upsert=True,
    )

    # Salva/atualiza cada track individualmente
    for track in tracks:
        tracks_collection.update_one(
            {"spotify_id": track["spotify_id"]},
            {"$set": {**track, "updated_at": now}},
            upsert=True,
        )


def get_tracks_by_ids(track_ids):
    """Busca tracks pelo spotify_id."""
    if not track_ids:
        return []
    cursor = tracks_collection.find({"spotify_id": {"$in": track_ids}})
    return list(cursor)


def get_random_tracks_from_pool(limit=20, exclude_seeds=True):
    """
    Retorna N tracks aleatórias do pool acumulado no MongoDB.
    Se exclude_seeds=True, exclui mocks e seeds.
    """
    match = {}
    if exclude_seeds:
        match = {
            "spotify_id": {
                "$not": {"$regex": "^(mock_|seed_)"}
            }
        }
    pipeline = [
        {"$match": match},
        {"$sample": {"size": limit}},
    ]
    return list(tracks_collection.aggregate(pipeline))


def get_all_tracks_from_pool(exclude_seeds=True):
    """
    Retorna TODAS as tracks do pool acumulado no MongoDB.
    Se exclude_seeds=True, exclui mocks e seeds.
    """
    match = {}
    if exclude_seeds:
        match = {
            "spotify_id": {
                "$not": {"$regex": "^(mock_|seed_)"}
            }
        }
    return list(tracks_collection.find(match))


def add_tracks_to_pool(tracks):
    """
    Adiciona tracks ao pool acumulado sem sobrescrever o feed do dia.
    Usa upsert para evitar duplicatas por spotify_id.
    """
    now = datetime.now(timezone.utc)
    for track in tracks:
        tracks_collection.update_one(
            {"spotify_id": track["spotify_id"]},
            {"$set": {**track, "updated_at": now}},
            upsert=True,
        )


def acquire_fetch_lock():
    """
    Tenta adquirir o lock diário para fazer fetch do RapidAPI.
    Retorna True se conseguiu (primeiro do dia), False se já foi feito.
    Usa insert_one atômico para evitar race conditions.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        fetch_lock_collection.insert_one({
            "_id": today,
            "date": today,
            "created_at": datetime.now(timezone.utc),
        })
        return True
    except Exception:
        # DuplicateKeyError → já existe lock para hoje
        return False


def was_pool_updated_today():
    """
    Verifica se alguma track do pool foi adicionada/atualizada hoje.
    """
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    match = {
        "updated_at": {"$gte": today_start},
        "spotify_id": {"$not": {"$regex": "^(mock_|seed_)"}}
    }
    return tracks_collection.count_documents(match) > 0


def get_last_pool_update():
    """Retorna a data da última track atualizada no pool."""
    track = tracks_collection.find_one(
        {"spotify_id": {"$not": {"$regex": "^(mock_|seed_)"}}},
        sort=[("updated_at", -1)]
    )
    if track and track.get("updated_at"):
        return track["updated_at"]
    return None


def count_pool_tracks(exclude_seeds=True):
    """Conta quantas tracks existem no pool."""
    match = {}
    if exclude_seeds:
        match = {
            "spotify_id": {
                "$not": {"$regex": "^(mock_|seed_)"}
            }
        }
    return tracks_collection.count_documents(match)


def update_track_sentiment(spotify_id, sentiment_score):
    """Atualiza o ajuste de sentimento de uma música."""
    tracks_collection.update_one(
        {"spotify_id": spotify_id},
        {"$set": {"sentiment_adjustment": round(sentiment_score, 1)}},
    )


def update_track_average(spotify_id, average, count):
    """Atualiza a média e contagem de avaliações de uma música."""
    tracks_collection.update_one(
        {"spotify_id": spotify_id},
        {"$set": {"average_rating": average, "rating_count": count}},
    )
