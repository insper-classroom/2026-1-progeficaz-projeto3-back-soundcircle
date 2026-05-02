"""Testes unitários para os modelos."""
import pytest


class TestUserModel:
    def test_create_and_get_user(self, client):
        from models.user import create_user, get_user_by_email, get_user_by_id
        user = create_user("model@example.com", "fakehash", "ModelUser")
        assert user["email"] == "model@example.com"
        assert user["display_name"] == "ModelUser"

        found = get_user_by_email("model@example.com")
        assert found is not None
        assert found["display_name"] == "ModelUser"

        by_id = get_user_by_id("model@example.com")
        assert by_id is not None

    def test_get_user_not_found(self, client):
        from models.user import get_user_by_email
        assert get_user_by_email("nonexistent@example.com") is None

    def test_get_user_by_display_name(self, client):
        from models.user import create_user, get_user_by_display_name
        create_user("disp@example.com", "hash", "DisplayName")
        found = get_user_by_display_name("DisplayName")
        assert found is not None
        assert found["email"] == "disp@example.com"

    def test_update_display_name(self, client):
        from models.user import create_user, update_display_name
        create_user("update@example.com", "hash", "Old")
        updated = update_display_name("update@example.com", "New")
        assert updated["display_name"] == "New"
        assert updated["display_name_lower"] == "new"


class TestRatingModel:
    def test_rate_track_and_average(self, client):
        from models.rating import rate_track, get_average_rating, get_user_rating
        rate_track("user1", "track_a", 4.0)
        rate_track("user2", "track_a", 2.0)
        avg = get_average_rating("track_a")
        assert avg["average"] == 3.0
        assert avg["count"] == 2

        user_r = get_user_rating("user1", "track_a")
        assert user_r["score"] == 4.0

    def test_delete_rating(self, client):
        from models.rating import rate_track, delete_user_rating, get_average_rating
        rate_track("user1", "track_b", 5.0)
        assert delete_user_rating("user1", "track_b") is True
        avg = get_average_rating("track_b")
        assert avg["count"] == 0

    def test_get_rated_tracks(self, client):
        from models.rating import rate_track, get_rated_tracks_by_user
        rate_track("user1", "track_c", 3.0)
        rated = get_rated_tracks_by_user("user1")
        assert len(rated) == 1
        assert rated[0]["track_id"] == "track_c"


class TestCommentModel:
    def test_add_and_get_comments(self, client):
        from models.comment import add_comment, get_comments_by_track
        add_comment("user1", "User One", "track_d", "Nice!")
        add_comment("user2", "User Two", "track_d", "Love it!")
        comments = get_comments_by_track("track_d")
        assert len(comments) == 2

    def test_delete_comment(self, client):
        from models.comment import add_comment, delete_comment, get_comments_by_track
        c = add_comment("user1", "User One", "track_e", "Delete me")
        assert delete_comment(c["_id"], "user1") is True
        assert len(get_comments_by_track("track_e")) == 0

    def test_delete_comment_wrong_user(self, client):
        from models.comment import add_comment, delete_comment
        c = add_comment("user1", "User One", "track_f", "No delete")
        assert delete_comment(c["_id"], "user2") is False


class TestFriendModel:
    def test_send_and_get_pending(self, client):
        from models.friend import send_friend_request, get_pending_requests
        send_friend_request("user_a", "user_b")
        pending = get_pending_requests("user_b")
        assert len(pending) == 1
        assert pending[0]["from_user_id"] == "user_a"

    def test_get_friends_accepted(self, client):
        from models.friend import send_friend_request, respond_to_request, get_friends, friend_requests_collection
        send_friend_request("user_a", "user_b")
        req = friend_requests_collection.find_one({"from_user_id": "user_a"})
        respond_to_request(str(req["_id"]), "accept")
        friends = get_friends("user_a")
        assert "user_b" in friends

    def test_remove_friendship(self, client):
        from models.friend import send_friend_request, respond_to_request, remove_friendship, friend_requests_collection
        send_friend_request("user_a", "user_b")
        req = friend_requests_collection.find_one({"from_user_id": "user_a"})
        respond_to_request(str(req["_id"]), "accept")
        assert remove_friendship("user_a", "user_b") is True
        from models.friend import get_friends
        assert get_friends("user_a") == []

    def test_get_friend_request_between(self, client):
        from models.friend import send_friend_request, get_friend_request_between
        send_friend_request("user_a", "user_b")
        req = get_friend_request_between("user_a", "user_b")
        assert req is not None
        assert req["status"] == "pending"


class TestPromotionModel:
    def test_create_and_get_active(self, client):
        from models.promotion import create_promotion, get_active_promotions
        promo = create_promotion("track_g", "user1", amount=25.0)
        assert promo["amount"] == 25.0
        assert promo["currency"] == "USD"
        active = get_active_promotions()
        assert len(active) == 1

    def test_get_active_for_track(self, client):
        from models.promotion import create_promotion, get_active_promotion_for_track
        create_promotion("track_h", "user1")
        found = get_active_promotion_for_track("track_h")
        assert found is not None
        assert found["track_id"] == "track_h"


class TestFeedModel:
    def test_save_and_get_feed(self, client):
        from models.feed import save_daily_feed, get_feed_for_date
        tracks = [{"spotify_id": "t1", "name": "Song1"}]
        save_daily_feed("2024-01-01", tracks)
        feed = get_feed_for_date("2024-01-01")
        assert feed is not None
        assert feed["date"] == "2024-01-01"

    def test_get_tracks_by_ids(self, client):
        from models.feed import add_tracks_to_pool, get_tracks_by_ids
        add_tracks_to_pool([{"spotify_id": "t2", "name": "Song2"}])
        tracks = get_tracks_by_ids(["t2"])
        assert len(tracks) == 1
        assert tracks[0]["name"] == "Song2"

    def test_update_track_sentiment_and_average(self, client):
        from models.feed import add_tracks_to_pool, update_track_sentiment, update_track_average, tracks_collection
        add_tracks_to_pool([{"spotify_id": "t3", "name": "Song3"}])
        update_track_sentiment("t3", 0.7)
        update_track_average("t3", 4.2, 10)
        track = tracks_collection.find_one({"spotify_id": "t3"})
        assert track["sentiment_adjustment"] == 0.7
        assert track["average_rating"] == 4.2
        assert track["rating_count"] == 10
