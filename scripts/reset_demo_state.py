"""Reset deterministic reference records in PostgreSQL and Redis."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

import redis.asyncio as redis
from demo_dataset import DEMO_TAGS, DEMO_USERS, build_demo_content
from seed_utils import (
    get_async_session,
    get_redis_url,
    print_error,
    print_step,
    print_success,
)
from sqlalchemy import bindparam, text


def _expanding_statement(sql: str, parameter_name: str):
    """Return a SQL text statement with an expanding parameter."""

    return text(sql).bindparams(bindparam(parameter_name, expanding=True))


async def _fetch_matching_ids(session, table_name: str, column_name: str, values: list[str]) -> set[str]:
    """Return identifiers from the given table that match the provided values."""

    if not values:
        return set()

    statement = _expanding_statement(
        f"SELECT id FROM {table_name} WHERE {column_name} IN :values",
        "values",
    )
    result = await session.execute(statement, {"values": values})
    return {str(value) for value in result.scalars().all()}


async def _delete_matching_rows(session, sql: str, parameter_name: str, values: list[str]) -> None:
    """Delete rows when there are values to bind."""

    if not values:
        return

    statement = _expanding_statement(sql, parameter_name)
    await session.execute(statement, {parameter_name: values})


async def _delete_redis_keys(redis_client: redis.Redis, keys: Iterable[str]) -> int:
    """Delete Redis keys if any exist."""

    resolved_keys = sorted(set(keys))
    if not resolved_keys:
        return 0
    return int(await redis_client.delete(*resolved_keys))


async def _scan_matching_keys(redis_client: redis.Redis, pattern: str) -> set[str]:
    """Return all keys matching the provided Redis pattern."""

    matches: set[str] = set()
    async for key in redis_client.scan_iter(match=pattern):
        matches.add(str(key))
    return matches


async def reset_demo_state() -> None:
    """Delete deterministic reference records from backing stores."""

    print_step("RESET", "Connecting to PostgreSQL and Redis...")
    async_session, engine = await get_async_session()
    redis_client = redis.from_url(get_redis_url(), decode_responses=True)

    demo_users = DEMO_USERS
    demo_content = build_demo_content()
    demo_tags = DEMO_TAGS

    canonical_user_ids = {str(user["id"]) for user in demo_users}
    canonical_profile_user_ids = list(canonical_user_ids)
    canonical_usernames = [str(user["username"]) for user in demo_users]
    canonical_emails = [str(user["email"]) for user in demo_users]
    canonical_content_ids = {str(item["id"]) for item in demo_content}
    canonical_titles = [str(item["title"]) for item in demo_content]
    canonical_tag_ids = {str(tag["id"]) for tag in demo_tags}
    canonical_tag_names = [str(tag["name"]) for tag in demo_tags]

    try:
        async with async_session() as session:
            user_ids = canonical_user_ids | await _fetch_matching_ids(
                session,
                "users",
                "username",
                canonical_usernames,
            ) | await _fetch_matching_ids(
                session,
                "users",
                "email",
                canonical_emails,
            )
            content_ids = canonical_content_ids | await _fetch_matching_ids(
                session,
                "content_items",
                "title",
                canonical_titles,
            )
            tag_ids = canonical_tag_ids | await _fetch_matching_ids(
                session,
                "content_tags",
                "name",
                canonical_tag_names,
            )

            user_id_list = sorted(user_ids)
            content_id_list = sorted(content_ids)
            tag_id_list = sorted(tag_ids)

            print_step("RESET", "Deleting reference rows from PostgreSQL...")
            await _delete_matching_rows(
                session,
                (
                    "DELETE FROM experiment_exposure_items "
                    "WHERE exposure_id IN (SELECT id FROM experiment_exposures WHERE user_id IN :user_ids)"
                ),
                "user_ids",
                user_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM experiment_exposures WHERE user_id IN :user_ids",
                "user_ids",
                user_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM experiment_assignments WHERE user_id IN :user_ids",
                "user_ids",
                user_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM interactions WHERE user_id IN :user_ids",
                "user_ids",
                user_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM interactions WHERE content_id IN :content_ids",
                "content_ids",
                content_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM content_feature_snapshots WHERE content_id IN :content_ids",
                "content_ids",
                content_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM user_topic_feature_snapshots WHERE user_id IN :user_ids",
                "user_ids",
                user_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM content_tags_association WHERE content_id IN :content_ids",
                "content_ids",
                content_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM content_tags_association WHERE tag_id IN :tag_ids",
                "tag_ids",
                tag_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM content_items WHERE id IN :content_ids",
                "content_ids",
                content_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM content_tags WHERE id IN :tag_ids",
                "tag_ids",
                tag_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM user_profiles WHERE user_id IN :user_ids",
                "user_ids",
                canonical_profile_user_ids + user_id_list,
            )
            await _delete_matching_rows(
                session,
                "DELETE FROM users WHERE id IN :user_ids",
                "user_ids",
                user_id_list,
            )
            await session.commit()

        print_step("RESET", "Deleting reference keys from Redis...")
        redis_keys: set[str] = set()
        for user_id in canonical_user_ids:
            redis_keys.add(f"feature:user:{user_id}:topic-affinity:v1")
            redis_keys |= await _scan_matching_keys(
                redis_client,
                f"feature:user:{user_id}:topic:*:metric:*:rolling-window:v1",
            )
            redis_keys |= await _scan_matching_keys(
                redis_client,
                f"feed:user:{user_id}:experiment:*",
            )
        for content_id in canonical_content_ids:
            redis_keys.add(f"feature:content:{content_id}:v1")
            redis_keys |= await _scan_matching_keys(
                redis_client,
                f"feature:content:{content_id}:metric:*:rolling-window:v1",
            )

        deleted_key_count = await _delete_redis_keys(redis_client, redis_keys)
        print_step("RESET", f"Removed {deleted_key_count} Redis keys")
    except Exception as exc:
        print_error(f"Failed to reset reference state: {exc}")
        raise
    finally:
        await redis_client.aclose()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(reset_demo_state())
    print_success("Reference state reset completed")
