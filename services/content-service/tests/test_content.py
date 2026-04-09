"""Tests for content endpoints."""


class TestContentEndpoints:
    """Test cases for content endpoints."""

    def test_create_tag_success(self, client):
        """Test successful tag creation."""

        response = client.post(
            "/api/v1/tags",
            json={"name": "Distributed-Systems", "description": "Distributed systems concepts"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "distributed-systems"
        assert "id" in data

    def test_create_content_success(self, client):
        """Test successful draft content creation with tags."""

        tag_response = client.post(
            "/api/v1/tags",
            json={"name": "api-design", "description": "API design patterns"},
        )
        tag_id = tag_response.json()["id"]

        response = client.post(
            "/api/v1/content",
            json={
                "title": "Introduction to Distributed Systems",
                "description": "A comprehensive guide to building distributed systems",
                "topic": "system-design",
                "category": "system-design",
                "status": "draft",
                "tag_ids": [tag_id],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Introduction to Distributed Systems"
        assert data["status"] == "draft"
        assert data["tags"][0]["id"] == tag_id
        assert data["published_at"] is None

    def test_create_content_with_unknown_tag_fails(self, client):
        """Test validation for missing tag IDs."""

        response = client.post(
            "/api/v1/content",
            json={
                "title": "Unknown Tag Example",
                "description": "Should fail",
                "topic": "backend",
                "category": "backend",
                "tag_ids": ["missing-tag-id"],
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Unknown tag IDs: missing-tag-id"

    def test_list_content_filters(self, client):
        """Test listing and filtering content by status and tag."""

        backend_tag = client.post(
            "/api/v1/tags",
            json={"name": "backend", "description": "Backend engineering"},
        ).json()["id"]
        ai_tag = client.post(
            "/api/v1/tags",
            json={"name": "ai", "description": "AI content"},
        ).json()["id"]

        client.post(
            "/api/v1/content",
            json={
                "title": "REST API Design Patterns",
                "description": "Backend patterns",
                "topic": "backend",
                "category": "backend",
                "status": "published",
                "tag_ids": [backend_tag],
            },
        )
        client.post(
            "/api/v1/content",
            json={
                "title": "Prompt Engineering Best Practices",
                "description": "AI prompting",
                "topic": "ai",
                "category": "ai",
                "status": "draft",
                "tag_ids": [ai_tag],
            },
        )

        response = client.get("/api/v1/content?status=published&tag=backend")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "published"
        assert data["items"][0]["category"] == "backend"

    def test_list_content_filters_without_duplicate_rows(self, client):
        """Filtered content listings should return unique content items."""

        backend_tag = client.post(
            "/api/v1/tags",
            json={"name": "backend-platform", "description": "Backend platform content"},
        ).json()["id"]
        architecture_tag = client.post(
            "/api/v1/tags",
            json={"name": "architecture", "description": "Architecture content"},
        ).json()["id"]

        published_response = client.post(
            "/api/v1/content",
            json={
                "title": "Reliable Service Boundaries",
                "description": "Boundary design for backend systems",
                "topic": "backend",
                "category": "backend",
                "status": "published",
                "tag_ids": [backend_tag, architecture_tag],
            },
        )
        published_content_id = published_response.json()["id"]

        response = client.get("/api/v1/content?status=published&tag=backend-platform")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == published_content_id

    def test_publish_content_success(self, client):
        """Test publishing a draft content item."""

        create_response = client.post(
            "/api/v1/content",
            json={
                "title": "Kubernetes Basics",
                "description": "Container orchestration essentials",
                "topic": "devops",
                "category": "devops",
            },
        )
        content_id = create_response.json()["id"]

        response = client.post(f"/api/v1/content/{content_id}/publish")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"
        assert data["published_at"] is not None

    def test_get_nonexistent_content(self, client):
        """Test retrieving a non-existent content item."""

        response = client.get("/api/v1/content/nonexistent-id")

        assert response.status_code == 404
        assert response.json()["detail"] == "Content 'nonexistent-id' not found"

    def test_root_endpoint(self, client):
        """Test root endpoint."""

        response = client.get("/")

        assert response.status_code == 200
        assert response.json()["service"] == "content-service"
