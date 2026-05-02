import pytest
import sys
import os

# Garante que o diretório raiz do projeto esteja no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from models.user import db as user_db


@pytest.fixture
def client():
    """Cliente de teste do Flask com banco de testes."""
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret"
    app.config["SECRET_KEY"] = "test-flask-secret"

    # Troca para banco de testes
    original_db_name = user_db.name
    test_db = user_db.client["soundcircle_test"]

    # Monkey-patch dos collections para apontar para o banco de testes
    import models.user
    import models.comment
    import models.feed
    import models.friend
    import models.promotion
    import models.rating
    import models.revoked_token

    models.user.users_collection = test_db.users
    models.comment.comments_collection = test_db.comments
    models.feed.tracks_collection = test_db.daily_tracks
    models.feed.feed_state_collection = test_db.feed_state
    models.feed.fetch_lock_collection = test_db.fetch_lock
    models.friend.friend_requests_collection = test_db.friend_requests
    models.promotion.promotions_collection = test_db.promoted_tracks
    models.rating.ratings_collection = test_db.ratings
    models.revoked_token.revoked_tokens_collection = test_db.revoked_tokens

    with app.test_client() as c:
        yield c

    # Limpa banco de testes após cada teste
    test_db.client.drop_database("soundcircle_test")
