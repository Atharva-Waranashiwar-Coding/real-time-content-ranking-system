"""Seed deterministic feature vectors and experiment analytics state."""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict

import redis.asyncio as redis
from demo_dataset import (
    build_content_feature_rows,
    build_experiment_assignments,
    build_experiment_exposures,
    build_user_topic_affinity_rows,
)
from seed_utils import (
    get_async_session,
    get_redis_url,
    print_error,
    print_step,
    print_success,
)
from sqlalchemy import bindparam, text

from shared_schemas import (
    ContentFeaturesV1Schema,
    InteractionEventV1Schema,
    UserTopicAffinityV1Schema,
)


def _expanding_statement(sql: str, parameter_name: str):
    """Return a SQL text statement with an expanding parameter."""

    return text(sql).bindparams(bindparam(parameter_name, expanding=True))


async def _delete_matching_rows(session, sql: str, parameter_name: str, values: list[str]) -> None:
    """Delete rows when there are values to bind."""

    if not values:
        return

    statement = _expanding_statement(sql, parameter_name)
    await session.execute(statement, {parameter_name: values})


def _content_feature_payload(row: dict[str, object]) -> dict[str, object]:
    """Return only shared-schema feature fields from a snapshot-ready row."""

    return {
        field_name: row[field_name]
        for field_name in ContentFeaturesV1Schema.model_fields
        if field_name in row
    }


def _content_feature_snapshot_row(
    schema: ContentFeaturesV1Schema,
    row: dict[str, object],
    index: int,
) -> dict[str, object]:
    """Build a PostgreSQL snapshot row without JSON-serializing datetimes."""

    return {
        "id": f"60000000-0000-0000-0000-{index:012d}",
        "schema_name": schema.schema_name,
        "content_id": str(schema.content_id),
        "topic": schema.topic,
        "window_hours": schema.window_hours,
        "impressions": schema.impressions,
        "clicks": schema.clicks,
        "likes": schema.likes,
        "saves": schema.saves,
        "skip_count": schema.skip_count,
        "watch_starts": schema.watch_starts,
        "watch_completes": schema.watch_completes,
        "ctr": schema.ctr,
        "like_rate": schema.like_rate,
        "save_rate": schema.save_rate,
        "skip_rate": schema.skip_rate,
        "completion_rate": schema.completion_rate,
        "trending_score": schema.trending_score,
        "last_event_at": schema.last_event_at,
        "snapshot_at": row["snapshot_at"],
        "created_at": row["snapshot_at"],
    }


async def seed_demo_state() -> None:
    """Seed Redis features plus experiment and interaction demo rows."""

    print_step("DEMO", "Connecting to PostgreSQL and Redis...")
    async_session, engine = await get_async_session()
    redis_client = redis.from_url(get_redis_url(), decode_responses=True)

    content_feature_rows = build_content_feature_rows()
    user_topic_rows = build_user_topic_affinity_rows()
    assignments = build_experiment_assignments()
    exposures = build_experiment_exposures()

    try:
        async with async_session() as session:
            print_step("DEMO", "Refreshing deterministic experiment and analytics rows...")
            assignment_user_ids = sorted({str(item["user_id"]) for item in assignments})
            content_ids = sorted({str(item["content_id"]) for item in content_feature_rows})
            interaction_ids = [
                str(interaction["id"])
                for exposure in exposures
                for interaction in exposure["interactions"]
            ]
            interaction_event_ids = [
                str(interaction["event_id"])
                for exposure in exposures
                for interaction in exposure["interactions"]
            ]

            await _delete_matching_rows(
                session,
                (
                    "DELETE FROM experiment_exposure_items "
                    "WHERE exposure_id IN (SELECT id FROM experiment_exposures WHERE user_id IN :user_ids)"
                ),
                "user_ids",
                assignment_user_ids,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM experiment_exposures WHERE user_id IN :user_ids",
                "user_ids",
                assignment_user_ids,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM experiment_assignments WHERE user_id IN :user_ids",
                "user_ids",
                assignment_user_ids,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM interactions WHERE id IN :interaction_ids",
                "interaction_ids",
                interaction_ids,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM interactions WHERE event_id IN :event_ids",
                "event_ids",
                interaction_event_ids,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM content_feature_snapshots WHERE content_id IN :content_ids",
                "content_ids",
                content_ids,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM user_topic_feature_snapshots WHERE user_id IN :user_ids",
                "user_ids",
                assignment_user_ids,
            )

            await session.execute(
                text(
                    """
                    INSERT INTO experiment_assignments (
                        id,
                        schema_name,
                        experiment_key,
                        variant_key,
                        strategy_name,
                        user_id,
                        assignment_bucket,
                        assigned_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :schema_name,
                        :experiment_key,
                        :variant_key,
                        :strategy_name,
                        :user_id,
                        :assignment_bucket,
                        :assigned_at,
                        :updated_at
                    )
                    """
                ),
                assignments,
            )

            exposure_rows = [
                {
                    "id": exposure["id"],
                    "schema_name": exposure["schema_name"],
                    "experiment_key": exposure["experiment_key"],
                    "variant_key": exposure["variant_key"],
                    "strategy_name": exposure["strategy_name"],
                    "user_id": exposure["user_id"],
                    "session_id": exposure["session_id"],
                    "request_id": exposure["request_id"],
                    "correlation_id": exposure["correlation_id"],
                    "feed_limit": exposure["feed_limit"],
                    "feed_offset": exposure["feed_offset"],
                    "cache_hit": exposure["cache_hit"],
                    "generated_at": exposure["generated_at"],
                    "created_at": exposure["created_at"],
                }
                for exposure in exposures
            ]
            await session.execute(
                text(
                    """
                    INSERT INTO experiment_exposures (
                        id,
                        schema_name,
                        experiment_key,
                        variant_key,
                        strategy_name,
                        user_id,
                        session_id,
                        request_id,
                        correlation_id,
                        feed_limit,
                        feed_offset,
                        cache_hit,
                        generated_at,
                        created_at
                    ) VALUES (
                        :id,
                        :schema_name,
                        :experiment_key,
                        :variant_key,
                        :strategy_name,
                        :user_id,
                        :session_id,
                        :request_id,
                        :correlation_id,
                        :feed_limit,
                        :feed_offset,
                        :cache_hit,
                        :generated_at,
                        :created_at
                    )
                    """
                ),
                exposure_rows,
            )

            exposure_item_rows = [
                {
                    "id": item["id"],
                    "exposure_id": exposure["id"],
                    "content_id": item["content_id"],
                    "rank": item["rank"],
                    "score": item["score"],
                    "topic": item["topic"],
                    "category": item["category"],
                    "created_at": item["created_at"],
                }
                for exposure in exposures
                for item in exposure["items"]
            ]
            await session.execute(
                text(
                    """
                    INSERT INTO experiment_exposure_items (
                        id,
                        exposure_id,
                        content_id,
                        rank,
                        score,
                        topic,
                        category,
                        created_at
                    ) VALUES (
                        :id,
                        :exposure_id,
                        :content_id,
                        :rank,
                        :score,
                        :topic,
                        :category,
                        :created_at
                    )
                    """
                ),
                exposure_item_rows,
            )

            interaction_rows = []
            for exposure in exposures:
                for interaction in exposure["interactions"]:
                    event = InteractionEventV1Schema(
                        event_id=interaction["event_id"],
                        event_type=interaction["event_type"],
                        user_id=interaction["user_id"],
                        content_id=interaction["content_id"],
                        session_id=interaction["session_id"],
                        topic=interaction["topic"],
                        watch_duration_seconds=interaction["watch_duration_seconds"],
                        event_timestamp=interaction["event_timestamp"],
                        metadata={
                            "surface": "demo_bootstrap",
                            "source": "scripts/seed_demo_state.py",
                        },
                    )
                    interaction_rows.append(
                        {
                            "id": interaction["id"],
                            "event_id": str(event.event_id),
                            "schema_name": event.schema_name,
                            "event_type": event.event_type,
                            "user_id": str(event.user_id),
                            "content_id": str(event.content_id),
                            "session_id": event.session_id,
                            "topic": event.topic,
                            "watch_duration_seconds": event.watch_duration_seconds,
                            "metadata_json": json.dumps(event.metadata, separators=(",", ":")),
                            "event_payload_json": json.dumps(
                                event.model_dump(mode="json"),
                                separators=(",", ":"),
                                sort_keys=True,
                            ),
                            "kafka_topic": "interactions.events.v1",
                            "request_id": interaction["request_id"],
                            "correlation_id": interaction["correlation_id"],
                            "event_timestamp": interaction["event_timestamp"],
                            "created_at": interaction["created_at"],
                            "published_at": interaction["published_at"],
                        }
                    )

            await session.execute(
                text(
                    """
                    INSERT INTO interactions (
                        id,
                        event_id,
                        schema_name,
                        event_type,
                        user_id,
                        content_id,
                        session_id,
                        topic,
                        watch_duration_seconds,
                        metadata,
                        event_payload,
                        kafka_topic,
                        request_id,
                        correlation_id,
                        event_timestamp,
                        created_at,
                        published_at
                    ) VALUES (
                        :id,
                        :event_id,
                        :schema_name,
                        :event_type,
                        :user_id,
                        :content_id,
                        :session_id,
                        :topic,
                        :watch_duration_seconds,
                        CAST(:metadata_json AS JSONB),
                        CAST(:event_payload_json AS JSONB),
                        :kafka_topic,
                        :request_id,
                        :correlation_id,
                        :event_timestamp,
                        :created_at,
                        :published_at
                    )
                    """
                ),
                interaction_rows,
            )

            content_snapshot_rows = []
            for index, row in enumerate(content_feature_rows, start=1):
                schema = ContentFeaturesV1Schema.model_validate(_content_feature_payload(row))
                content_snapshot_rows.append(
                    _content_feature_snapshot_row(schema=schema, row=row, index=index)
                )
            await session.execute(
                text(
                    """
                    INSERT INTO content_feature_snapshots (
                        id,
                        schema_name,
                        content_id,
                        topic,
                        window_hours,
                        impressions,
                        clicks,
                        likes,
                        saves,
                        skip_count,
                        watch_starts,
                        watch_completes,
                        ctr,
                        like_rate,
                        save_rate,
                        skip_rate,
                        completion_rate,
                        trending_score,
                        last_event_at,
                        snapshot_at,
                        created_at
                    ) VALUES (
                        :id,
                        :schema_name,
                        :content_id,
                        :topic,
                        :window_hours,
                        :impressions,
                        :clicks,
                        :likes,
                        :saves,
                        :skip_count,
                        :watch_starts,
                        :watch_completes,
                        :ctr,
                        :like_rate,
                        :save_rate,
                        :skip_rate,
                        :completion_rate,
                        :trending_score,
                        :last_event_at,
                        :snapshot_at,
                        :created_at
                    )
                    """
                ),
                content_snapshot_rows,
            )

            user_affinity_map: dict[str, dict[str, float]] = defaultdict(dict)
            user_snapshot_rows = []
            for row in user_topic_rows:
                user_affinity_map[str(row["user_id"])][str(row["topic"])] = float(row["affinity_score"])
                user_snapshot_rows.append(
                    {
                        "id": f"61000000-0000-0000-0000-{len(user_snapshot_rows) + 1:012d}",
                        "schema_name": "user_topic_affinity.v1",
                        "user_id": row["user_id"],
                        "topic": row["topic"],
                        "window_hours": row["window_hours"],
                        "impressions": row["impressions"],
                        "clicks": row["clicks"],
                        "likes": row["likes"],
                        "saves": row["saves"],
                        "skip_count": row["skip_count"],
                        "watch_starts": row["watch_starts"],
                        "watch_completes": row["watch_completes"],
                        "affinity_score": row["affinity_score"],
                        "last_event_at": row["last_event_at"],
                        "snapshot_at": row["snapshot_at"],
                        "created_at": row["snapshot_at"],
                    }
                )
            await session.execute(
                text(
                    """
                    INSERT INTO user_topic_feature_snapshots (
                        id,
                        schema_name,
                        user_id,
                        topic,
                        window_hours,
                        impressions,
                        clicks,
                        likes,
                        saves,
                        skip_count,
                        watch_starts,
                        watch_completes,
                        affinity_score,
                        last_event_at,
                        snapshot_at,
                        created_at
                    ) VALUES (
                        :id,
                        :schema_name,
                        :user_id,
                        :topic,
                        :window_hours,
                        :impressions,
                        :clicks,
                        :likes,
                        :saves,
                        :skip_count,
                        :watch_starts,
                        :watch_completes,
                        :affinity_score,
                        :last_event_at,
                        :snapshot_at,
                        :created_at
                    )
                    """
                ),
                user_snapshot_rows,
            )

            await session.commit()

        print_step("DEMO", "Writing low-latency feature hashes to Redis...")
        for row in content_feature_rows:
            schema = ContentFeaturesV1Schema.model_validate(_content_feature_payload(row))
            await redis_client.hset(
                f"feature:content:{schema.content_id}:v1",
                mapping=schema.model_dump(mode="json"),
            )

        for user_id, topic_affinity in user_affinity_map.items():
            affinity_schema = UserTopicAffinityV1Schema(
                user_id=user_id,
                topic_affinity=topic_affinity,
                last_event_at=max(
                    row["last_event_at"]
                    for row in user_topic_rows
                    if str(row["user_id"]) == user_id
                ),
                updated_at=max(
                    row["updated_at"]
                    for row in user_topic_rows
                    if str(row["user_id"]) == user_id
                ),
            )
            payload = affinity_schema.model_dump(mode="json")
            flattened_mapping: dict[str, object] = {
                "schema_name": payload["schema_name"],
                "user_id": payload["user_id"],
                "window_hours": payload["window_hours"],
                "last_event_at": payload["last_event_at"],
                "updated_at": payload["updated_at"],
            }
            for topic, affinity_score in payload["topic_affinity"].items():
                flattened_mapping[f"topic_affinity.{topic}"] = affinity_score
            await redis_client.hset(
                f"feature:user:{user_id}:topic-affinity:v1",
                mapping=flattened_mapping,
            )

        print_step(
            "DEMO",
            (
                f"Seeded {len(content_feature_rows)} content feature rows, "
                f"{len(user_topic_rows)} user-topic rows, "
                f"{len(assignments)} assignments, and {len(exposures)} exposures"
            ),
        )
    except Exception as exc:
        print_error(f"Failed to seed demo state: {exc}")
        raise
    finally:
        await redis_client.aclose()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_demo_state())
    print_success("Deterministic demo state seeded")
