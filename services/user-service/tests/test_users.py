"""Tests for user endpoints."""


class TestUserEndpoints:
    """Test cases for user endpoints."""

    def test_create_user_success(self, client):
        """Test successful user creation with profile payload."""

        request_data = {
            "username": "john_doe",
            "email": "john@example.com",
            "profile": {
                "bio": "Backend engineer",
                "topic_preferences": {
                    "backend": 0.95,
                    "system-design": 0.8,
                    "ai": 0.45,
                },
            },
        }

        response = client.post("/api/v1/users", json=request_data)

        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "john_doe"
        assert data["email"] == "john@example.com"
        assert data["profile"]["bio"] == "Backend engineer"
        assert data["profile"]["topic_preferences"]["backend"] == 0.95

    def test_create_user_invalid_email(self, client):
        """Test user creation with invalid email."""

        response = client.post(
            "/api/v1/users",
            json={"username": "john_doe", "email": "invalid-email"},
        )

        assert response.status_code == 422

    def test_create_user_rejects_unknown_topic(self, client):
        """Test user creation with unsupported topic preferences."""

        response = client.post(
            "/api/v1/users",
            json={
                "username": "ranking_fan",
                "email": "ranking@example.com",
                "profile": {
                    "topic_preferences": {
                        "quantum-computing": 0.7,
                    }
                },
            },
        )

        assert response.status_code == 422

    def test_update_user_success(self, client):
        """Test updating username and email."""

        create_response = client.post(
            "/api/v1/users",
            json={"username": "alex_dev", "email": "alex@example.com"},
        )
        user_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/users/{user_id}",
            json={"username": "alex_platform", "email": "alex.platform@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "alex_platform"
        assert data["email"] == "alex.platform@example.com"

    def test_update_profile_and_topics(self, client):
        """Test profile and topic preference updates."""

        create_response = client.post(
            "/api/v1/users",
            json={"username": "emma_dev", "email": "emma@example.com"},
        )
        user_id = create_response.json()["id"]

        profile_response = client.put(
            f"/api/v1/users/{user_id}/profile",
            json={
                "bio": "Principal engineer focused on ranking systems",
                "topic_preferences": {"ai": 0.9, "backend": 0.8, "system-design": 0.7},
            },
        )

        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["bio"] == "Principal engineer focused on ranking systems"
        assert profile_data["topic_preferences"]["ai"] == 0.9

        topic_response = client.put(
            f"/api/v1/users/{user_id}/topics",
            json={
                "topic_preferences": {
                    "ai": 0.95,
                    "backend": 0.6,
                    "system-design": 0.75,
                    "devops": 0.4,
                    "interview-prep": 0.2,
                }
            },
        )

        assert topic_response.status_code == 200
        topic_data = topic_response.json()
        assert topic_data["topic_preferences"]["devops"] == 0.4
        assert topic_data["topic_preferences"]["interview-prep"] == 0.2

    def test_list_users(self, client):
        """Test listing users."""

        client.post("/api/v1/users", json={"username": "user_one", "email": "user1@example.com"})
        client.post("/api/v1/users", json={"username": "user_two", "email": "user2@example.com"})

        response = client.get("/api/v1/users?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_get_nonexistent_user(self, client):
        """Test retrieving a non-existent user."""

        response = client.get("/api/v1/users/nonexistent-id")

        assert response.status_code == 404
        assert response.json()["detail"] == "User 'nonexistent-id' not found"

    def test_root_endpoint(self, client):
        """Test root endpoint."""

        response = client.get("/")

        assert response.status_code == 200
        assert response.json()["service"] == "user-service"
