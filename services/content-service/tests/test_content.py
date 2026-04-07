"""Tests for content endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


class TestContentEndpoints:
    """Test cases for content endpoints."""

    def test_create_tag_success(self, client):
        """Test successful tag creation."""
        request_data = {
            "name": "python",
            "description": "Python programming language",
        }
        response = client.post("/api/v1/tags", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "python"
        assert "id" in data

    def test_list_tags(self, client):
        """Test listing tags."""
        response = client.get("/api/v1/tags")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_content_success(self, client):
        """Test successful content creation."""
        request_data = {
            "title": "Introduction to Distributed Systems",
            "description": "A comprehensive guide to building distributed systems",
            "topic": "system-design",
            "category": "system-design",
        }
        response = client.post("/api/v1/content", json=request_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Introduction to Distributed Systems"
        assert data["status"] == "draft"
        assert "id" in data

    def test_list_content(self, client):
        """Test listing content items."""
        response = client.get("/api/v1/content")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_get_nonexistent_content(self, client):
        """Test retrieving a non-existent content item."""
        response = client.get("/api/v1/content/nonexistent-id")
        
        assert response.status_code == 404

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "content-service"
