"""Testes para o blueprint de usuário."""


class TestProfile:
    def test_get_profile(self, client):
        client.post("/api/auth/register", json={
            "email": "prof@example.com",
            "password": "123456",
            "display_name": "ProfUser",
        })
        resp = client.get("/api/user/profile")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["email"] == "prof@example.com"
        assert data["display_name"] == "ProfUser"

    def test_get_profile_unauthenticated(self, client):
        resp = client.get("/api/user/profile")
        assert resp.status_code == 401


class TestUpdateProfile:
    def test_patch_display_name(self, client):
        client.post("/api/auth/register", json={
            "email": "patch@example.com",
            "password": "123456",
            "display_name": "OldName",
        })
        resp = client.patch("/api/user/profile", json={"display_name": "NewName"})
        assert resp.status_code == 200
        assert resp.get_json()["display_name"] == "NewName"

    def test_put_display_name_legacy(self, client):
        client.post("/api/auth/register", json={
            "email": "put@example.com",
            "password": "123456",
            "display_name": "OldName",
        })
        resp = client.put("/api/user/display-name", json={"display_name": "NewName2"})
        assert resp.status_code == 200
        assert resp.get_json()["display_name"] == "NewName2"

    def test_update_display_name_duplicate(self, client):
        client.post("/api/auth/register", json={
            "email": "user1@example.com",
            "password": "123456",
            "display_name": "NameOne",
        })
        client.post("/api/auth/register", json={
            "email": "user2@example.com",
            "password": "123456",
            "display_name": "NameTwo",
        })
        # Volta a estar logado como user1
        client.post("/api/auth/login", json={
            "email": "user1@example.com",
            "password": "123456",
        })
        # Tenta mudar user1 para NameTwo
        resp = client.patch("/api/user/profile", json={"display_name": "NameTwo"})
        assert resp.status_code == 409
        assert "já está em uso" in resp.get_json()["error"]

    def test_update_display_name_empty(self, client):
        client.post("/api/auth/register", json={
            "email": "empty@example.com",
            "password": "123456",
            "display_name": "EmptyUser",
        })
        resp = client.patch("/api/user/profile", json={"display_name": ""})
        assert resp.status_code == 400
        assert "obrigatório" in resp.get_json()["error"]


class TestRatedTracks:
    def test_rated_tracks_empty(self, client):
        client.post("/api/auth/register", json={
            "email": "rated@example.com",
            "password": "123456",
            "display_name": "RatedUser",
        })
        resp = client.get("/api/user/rated-tracks")
        assert resp.status_code == 200
        assert resp.get_json()["ratings"] == []

    def test_rated_tracks_with_data(self, client):
        client.post("/api/auth/register", json={
            "email": "rated2@example.com",
            "password": "123456",
            "display_name": "RatedUser2",
        })
        # Adiciona uma track ao pool e avalia
        from models.feed import add_tracks_to_pool
        add_tracks_to_pool([{
            "spotify_id": "track_001",
            "name": "Song One",
            "artist": "Artist A",
            "album": "Album A",
            "cover_url": "http://example.com/cover.jpg",
        }])
        client.post("/api/feed/tracks/track_001/ratings", json={"score": 4.5})

        resp = client.get("/api/user/rated-tracks")
        assert resp.status_code == 200
        ratings = resp.get_json()["ratings"]
        assert len(ratings) == 1
        assert ratings[0]["track_id"] == "track_001"
        assert ratings[0]["score"] == 4.5
