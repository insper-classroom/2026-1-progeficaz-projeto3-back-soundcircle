"""Testes para o blueprint de amizades."""


def _register(client, email, display_name):
    return client.post("/api/auth/register", json={
        "email": email,
        "password": "123456",
        "display_name": display_name,
    })


def _login(client, email):
    return client.post("/api/auth/login", json={
        "email": email,
        "password": "123456",
    })


class TestListFriends:
    def test_list_friends_empty(self, client):
        _register(client, "alone@example.com", "Alone")
        resp = client.get("/api/friends")
        assert resp.status_code == 200
        assert resp.get_json()["friends"] == []

    def test_list_friends_with_friend(self, client):
        _register(client, "user1@example.com", "User1")
        # Cria user2 diretamente no modelo de usuários
        from models.user import create_user
        create_user("user2@example.com", "fakehash", "User2")
        # Cria amizade diretamente no modelo
        from models.friend import send_friend_request, respond_to_request, friend_requests_collection
        send_friend_request("user1@example.com", "user2@example.com")
        request_doc = friend_requests_collection.find_one({
            "from_user_id": "user1@example.com",
            "to_user_id": "user2@example.com",
        })
        respond_to_request(str(request_doc["_id"]), "accept")

        resp = client.get("/api/friends")
        assert resp.status_code == 200
        friends = resp.get_json()["friends"]
        assert len(friends) == 1
        assert friends[0]["id"] == "user2@example.com"


class TestPendingRequests:
    def test_pending_requests(self, client):
        _register(client, "target@example.com", "Target")
        # Simula outro usuário enviando solicitação
        from models.friend import send_friend_request
        send_friend_request("other@example.com", "target@example.com")

        resp = client.get("/api/friends/pending")
        assert resp.status_code == 200
        requests = resp.get_json()["requests"]
        assert len(requests) == 1
        assert requests[0]["from_user_id"] == "other@example.com"


class TestSendRequest:
    def test_send_request_success(self, client):
        _register(client, "sender@example.com", "Sender")
        _register(client, "receiver@example.com", "Receiver")
        # Volta a estar logado como sender
        _login(client, "sender@example.com")

        resp = client.post("/api/friends", json={"display_name": "Receiver"})
        assert resp.status_code == 201
        assert "enviada" in resp.get_json()["message"]

    def test_send_request_self(self, client):
        _register(client, "self@example.com", "Self")
        resp = client.post("/api/friends", json={"display_name": "Self"})
        assert resp.status_code == 400
        assert "a si mesmo" in resp.get_json()["error"]

    def test_send_request_not_found(self, client):
        _register(client, "ghost@example.com", "Ghost")
        resp = client.post("/api/friends", json={"display_name": "NonExistent"})
        assert resp.status_code == 404
        assert "não encontrado" in resp.get_json()["error"]

    def test_send_request_already_friends(self, client):
        _register(client, "a@example.com", "UserA")
        _register(client, "b@example.com", "UserB")
        from models.friend import send_friend_request, respond_to_request, friend_requests_collection
        send_friend_request("a@example.com", "b@example.com")
        req = friend_requests_collection.find_one({"from_user_id": "a@example.com"})
        respond_to_request(str(req["_id"]), "accept")

        # Volta a estar logado como a
        _login(client, "a@example.com")
        resp = client.post("/api/friends", json={"display_name": "UserB"})
        assert resp.status_code == 409
        assert "já são amigos" in resp.get_json()["error"]


class TestRespondRequest:
    def test_accept_request(self, client):
        _register(client, "resp@example.com", "Resp")
        from models.friend import send_friend_request, friend_requests_collection
        send_friend_request("other@example.com", "resp@example.com")
        req = friend_requests_collection.find_one({"to_user_id": "resp@example.com"})

        resp = client.patch(f"/api/friends/requests/{req['_id']}", json={"action": "accept"})
        assert resp.status_code == 204

    def test_reject_request(self, client):
        _register(client, "rej@example.com", "Rej")
        from models.friend import send_friend_request, friend_requests_collection
        send_friend_request("other2@example.com", "rej@example.com")
        req = friend_requests_collection.find_one({"to_user_id": "rej@example.com"})

        resp = client.patch(f"/api/friends/requests/{req['_id']}", json={"action": "reject"})
        assert resp.status_code == 204

    def test_respond_invalid_action(self, client):
        _register(client, "inv@example.com", "Inv")
        resp = client.patch("/api/friends/requests/123456789012345678901234", json={"action": "nope"})
        assert resp.status_code == 400

    def test_respond_not_found(self, client):
        _register(client, "nf@example.com", "NF")
        resp = client.patch("/api/friends/requests/123456789012345678901234", json={"action": "accept"})
        assert resp.status_code == 404


class TestRemoveFriend:
    def test_remove_friend(self, client):
        _register(client, "rem1@example.com", "Rem1")
        from models.friend import send_friend_request, respond_to_request, friend_requests_collection
        send_friend_request("rem1@example.com", "rem2@example.com")
        req = friend_requests_collection.find_one({"from_user_id": "rem1@example.com"})
        respond_to_request(str(req["_id"]), "accept")

        resp = client.delete("/api/friends/rem2@example.com")
        assert resp.status_code == 204

    def test_remove_not_friend(self, client):
        _register(client, "rem3@example.com", "Rem3")
        resp = client.delete("/api/friends/stranger@example.com")
        assert resp.status_code == 403
        assert "não são amigos" in resp.get_json()["error"]


class TestFriendRatings:
    def test_friend_ratings(self, client):
        _register(client, "fr1@example.com", "Fr1")
        from models.friend import send_friend_request, respond_to_request, friend_requests_collection
        from models.rating import rate_track
        from models.feed import add_tracks_to_pool

        send_friend_request("fr1@example.com", "fr2@example.com")
        req = friend_requests_collection.find_one({"from_user_id": "fr1@example.com"})
        respond_to_request(str(req["_id"]), "accept")

        add_tracks_to_pool([{
            "spotify_id": "track_fr",
            "name": "Friend Song",
            "artist": "Friend Artist",
            "album": "Friend Album",
            "cover_url": "http://example.com/cover.jpg",
        }])
        rate_track("fr2@example.com", "track_fr", 5.0)

        resp = client.get("/api/friends/fr2@example.com/ratings")
        assert resp.status_code == 200
        ratings = resp.get_json()["ratings"]
        assert len(ratings) == 1
        assert ratings[0]["score"] == 5.0

    def test_friend_ratings_not_friend(self, client):
        _register(client, "nf1@example.com", "NF1")
        resp = client.get("/api/friends/stranger@example.com/ratings")
        assert resp.status_code == 403
        assert "não são amigos" in resp.get_json()["error"]
