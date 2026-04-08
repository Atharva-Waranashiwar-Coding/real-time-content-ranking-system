"""Tests for experimentation-service assignment and exposure APIs."""

from uuid import uuid4


class TestExperimentEndpoints:
    """Endpoint tests for experimentation-service."""

    def test_assignment_is_deterministic_for_same_user(self, client):
        """The same user should receive the same variant and strategy repeatedly."""

        user_id = str(uuid4())

        first_response = client.get(f"/api/v1/experiments/assignment?user_id={user_id}")
        second_response = client.get(f"/api/v1/experiments/assignment?user_id={user_id}")

        assert first_response.status_code == 200
        assert second_response.status_code == 200
        first_data = first_response.json()
        second_data = second_response.json()
        assert first_data["experiment_key"] == "home_feed_ranking.v1"
        assert first_data["variant_key"] == second_data["variant_key"]
        assert first_data["strategy_name"] == second_data["strategy_name"]
        assert first_data["assignment_bucket"] == second_data["assignment_bucket"]

    def test_record_exposure_persists_item_level_payload(self, client):
        """A valid exposure request should be accepted after assignment."""

        user_id = str(uuid4())
        assignment = client.get(
            f"/api/v1/experiments/assignment?user_id={user_id}"
        ).json()

        response = client.post(
            "/api/v1/experiments/exposures",
            json={
                "experiment_key": assignment["experiment_key"],
                "variant_key": assignment["variant_key"],
                "strategy_name": assignment["strategy_name"],
                "user_id": user_id,
                "session_id": "demo-session-001",
                "feed_limit": 10,
                "feed_offset": 0,
                "cache_hit": False,
                "items": [
                    {
                        "content_id": str(uuid4()),
                        "rank": 1,
                        "score": 0.72,
                        "topic": "backend",
                        "category": "backend",
                    }
                ],
            },
            headers={"X-Request-ID": "req-1", "X-Correlation-ID": "corr-1"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["experiment_key"] == assignment["experiment_key"]
        assert data["variant_key"] == assignment["variant_key"]
        assert data["strategy_name"] == assignment["strategy_name"]
        assert data["exposure_id"] is not None

    def test_record_exposure_rejects_assignment_mismatch(self, client):
        """The exposure payload should be rejected if it disagrees with the stored assignment."""

        user_id = str(uuid4())
        assignment = client.get(
            f"/api/v1/experiments/assignment?user_id={user_id}"
        ).json()

        response = client.post(
            "/api/v1/experiments/exposures",
            json={
                "experiment_key": assignment["experiment_key"],
                "variant_key": "unexpected_variant",
                "strategy_name": assignment["strategy_name"],
                "user_id": user_id,
                "feed_limit": 10,
                "feed_offset": 0,
                "cache_hit": False,
                "items": [],
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == (
            "Exposure variant does not match stored assignment"
        )
