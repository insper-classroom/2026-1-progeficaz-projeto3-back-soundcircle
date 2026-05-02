from datetime import datetime, timezone
from pymongo import ASCENDING
from models.user import db

revoked_tokens_collection = db.revoked_tokens

# Índice TTL: remove documentos automaticamente quando exp < now
revoked_tokens_collection.create_index(
    [("exp", ASCENDING)],
    expireAfterSeconds=0,
    name="ttl_exp"
)


def revoke_token(jti, exp):
    revoked_tokens_collection.insert_one({
        "jti": jti,
        "exp": datetime.fromtimestamp(exp, tz=timezone.utc),
        "revoked_at": datetime.now(timezone.utc),
    })


def is_token_revoked(jti):
    return revoked_tokens_collection.find_one({"jti": jti}) is not None
