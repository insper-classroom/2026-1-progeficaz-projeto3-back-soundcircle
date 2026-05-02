"""Testes para o blueprint de feed."""


def _register(client, email, display_name):
    return client.post("/api/auth/register", json={
        "email": email,
        "password": "123456",
        "display_name": display_name,
    })


class TestDailyFeed:
    def test_daily_feed(self, client):
        _register(client, "feed@example.com", "FeedUser")
        resp = client.get("/api/feed/daily?period=daily")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["period"] == "daily"
        assert "tracks" in data

    def test_weekly_feed(self, client):
        _register(client, "week@example.com", "WeekUser")
        resp = client.get("/api/feed/daily?period=weekly")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["period"] == "weekly"

    def test_monthly_feed(self, client):
        _register(client, "month@example.com", "MonthUser")
        resp = client.get("/api/feed/daily?period=monthly")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["period"] == "monthly"

    def test_invalid_period(self, client):
        _register(client, "invp@example.com", "InvPeriod")
        resp = client.get("/api/feed/daily?period=yearly")
        assert resp.status_code == 400
        assert "daily, weekly ou monthly" in resp.get_json()["error"]

    def test_feed_sort_best(self, client):
        _register(client, "sort@example.com", "SortUser")
        resp = client.get("/api/feed/daily?period=daily&sort=best")
        assert resp.status_code == 200
        assert "tracks" in resp.get_json()


class TestRatings:
    def test_create_rating(self, client):
        _register(client, "rate@example.com", "RateUser")
        from models.feed import add_tracks_to_pool
        add_tracks_to_pool([{
            "spotify_id": "track_rate",
            "name": "Rate Song",
            "artist": "Artist",
            "album": "Album",
            "cover_url": "http://example.com/cover.jpg",
        }])
        resp = client.post("/api/feed/tracks/track_rate/ratings", json={"score": 4.5})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["score"] == 4.5
        assert data["track_id"] == "track_rate"

    def test_create_rating_invalid_score(self, client):
        _register(client, "invrate@example.com", "InvRate")
        resp = client.post("/api/feed/tracks/track_xyz/ratings", json={"score": 10})
        assert resp.status_code == 422
        assert "1.0 e 5.0" in resp.get_json()["error"]

    def test_delete_rating(self, client):
        _register(client, "delrate@example.com", "DelRate")
        from models.feed import add_tracks_to_pool
        add_tracks_to_pool([{
            "spotify_id": "track_del",
            "name": "Del Song",
            "artist": "Artist",
            "album": "Album",
            "cover_url": "http://example.com/cover.jpg",
        }])
        client.post("/api/feed/tracks/track_del/ratings", json={"score": 3.0})
        resp = client.delete("/api/feed/tracks/track_del/ratings")
        assert resp.status_code == 204

    def test_delete_rating_not_found(self, client):
        _register(client, "nfrate@example.com", "NFRate")
        resp = client.delete("/api/feed/tracks/track_none/ratings")
        assert resp.status_code == 404


class TestComments:
    def test_create_comment(self, client):
        _register(client, "comm@example.com", "CommUser")
        from models.feed import add_tracks_to_pool
        add_tracks_to_pool([{
            "spotify_id": "track_comm",
            "name": "Comm Song",
            "artist": "Artist",
            "album": "Album",
            "cover_url": "http://example.com/cover.jpg",
        }])
        resp = client.post("/api/feed/tracks/track_comm/comments", json={"text": "Great song!"})
        assert resp.status_code == 201
        assert resp.get_json()["message"] == "Comentário adicionado."

    def test_list_comments(self, client):
        _register(client, "lcomm@example.com", "LCommUser")
        from models.feed import add_tracks_to_pool
        add_tracks_to_pool([{
            "spotify_id": "track_lcomm",
            "name": "LComm Song",
            "artist": "Artist",
            "album": "Album",
            "cover_url": "http://example.com/cover.jpg",
        }])
        client.post("/api/feed/tracks/track_lcomm/comments", json={"text": "Nice!"})
        resp = client.get("/api/feed/tracks/track_lcomm/comments")
        assert resp.status_code == 200
        assert len(resp.get_json()["comments"]) == 1

    def test_delete_comment(self, client):
        _register(client, "dcomm@example.com", "DCommUser")
        from models.feed import add_tracks_to_pool
        from models.comment import get_comments_by_track
        add_tracks_to_pool([{
            "spotify_id": "track_dcomm",
            "name": "DComm Song",
            "artist": "Artist",
            "album": "Album",
            "cover_url": "http://example.com/cover.jpg",
        }])
        client.post("/api/feed/tracks/track_dcomm/comments", json={"text": "Delete me"})
        comment = get_comments_by_track("track_dcomm")[0]
        resp = client.delete(f"/api/feed/tracks/track_dcomm/comments/{comment['_id']}")
        assert resp.status_code == 204

    def test_delete_comment_not_found(self, client):
        _register(client, "nfcomm@example.com", "NFComm")
        resp = client.delete("/api/feed/tracks/track_x/comments/123456789012345678901234")
        assert resp.status_code == 404


class TestPromote:
    def test_promote_track(self, client):
        _register(client, "promo@example.com", "PromoUser")
        from models.feed import add_tracks_to_pool
        add_tracks_to_pool([{
            "spotify_id": "track_promo",
            "name": "Promo Song",
            "artist": "Artist",
            "album": "Album",
            "cover_url": "http://example.com/cover.jpg",
        }])
        resp = client.post("/api/feed/promote", json={"track_id": "track_promo"})
        assert resp.status_code == 201
        data = resp.get_json()
        assert "impulsionada" in data["message"]
        assert data["amount"] == 25.0

    def test_promote_track_not_found(self, client):
        _register(client, "nfpromo@example.com", "NFPromo")
        resp = client.post("/api/feed/promote", json={"track_id": "track_none"})
        assert resp.status_code == 404
        assert "não encontrada" in resp.get_json()["error"]

    def test_promote_missing_track_id(self, client):
        _register(client, "misspromo@example.com", "MissPromo")
        resp = client.post("/api/feed/promote", json={})
        assert resp.status_code == 400
        assert "obrigatório" in resp.get_json()["error"]


class TestSentiment:
    def test_get_sentiment(self, client):
        _register(client, "sent@example.com", "SentUser")
        from models.feed import add_tracks_to_pool, update_track_sentiment
        add_tracks_to_pool([{
            "spotify_id": "track_sent",
            "name": "Sent Song",
            "artist": "Artist",
            "album": "Album",
            "cover_url": "http://example.com/cover.jpg",
        }])
        update_track_sentiment("track_sent", 0.5)
        resp = client.get("/api/feed/tracks/track_sent/sentiment")
        assert resp.status_code == 200
        assert resp.get_json()["sentiment_adjustment"] == 0.5

    def test_get_sentiment_not_found(self, client):
        _register(client, "nfsent@example.com", "NFSent")
        resp = client.get("/api/feed/tracks/track_none/sentiment")
        assert resp.status_code == 404
