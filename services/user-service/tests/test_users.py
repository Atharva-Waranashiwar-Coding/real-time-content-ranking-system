"""Tests for user endpoints."""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.user import UserCreateRequest


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


class TestUserEndpoints:
    """Test cases for user endpoints."""

    def test_create_user_success(self, client):
        """Test successful user creation."""
        request_data = {
            "username": "john_doe",
            "email": "john@example.com",
        }
        response = client.post("/api/v1/users", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "john_doe"
        assert data["email"] == "john@example.com"
        assert "id" in data
        assert "profile" in data

    def test_create_user_invalid_email(self, client):
        """Test user creation with invalid email."""
        request_data = {
            "username": "john_doe",
            "email": "invalid-email",
        }
        response = client.post("/api/v1/users", json=request_data)
        
        assert response.status_code == 422  # Validation error

    def test_create_user_short_username(self, client):
        """Test user creation with short username."""
        request_data = {
            "username": "ab",
            "email": "test@example.com",
        }
        response = client.post("/api/v1/users", json=request_data)
        
        assert response.status_code == 422  # Validation error

    def test_list_users(self, client):
        """Test listing users."""
        response = client.get("/api/v1/users")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_nonexistent_user(self, client):
        """Test retrieving a non-existent user."""
        response = client.get("/api/v1/users/nonexistent-id")
        
        assert response.status_code == 404

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "user-service"
