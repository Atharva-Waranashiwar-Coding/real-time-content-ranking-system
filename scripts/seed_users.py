"""Seed script for demo users."""

import asyncio
import sys
from pathlib import Path

from seed_utils import get_async_session, print_error, print_step, print_success
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "user-service"))

from app.models import User, UserProfile

DEMO_USERS = [
    {
        "username": "alice_dev",
        "email": "alice@example.com",
        "bio": "Platform-focused engineer learning how ranking systems personalize AI-heavy feeds.",
        "topic_preferences": {
            "ai": 0.92,
            "backend": 0.68,
            "system-design": 0.81,
            "devops": 0.35,
            "interview-prep": 0.24,
        },
    },
    {
        "username": "bob_engineer",
        "email": "bob@example.com",
        "bio": "Backend engineer who gravitates toward APIs, databases, and reliable production systems.",
        "topic_preferences": {
            "ai": 0.31,
            "backend": 0.96,
            "system-design": 0.85,
            "devops": 0.62,
            "interview-prep": 0.18,
        },
    },
    {
        "username": "charlie_sysadmin",
        "email": "charlie@example.com",
        "bio": "Infra-minded operator interested in observability, containers, and resilient architecture.",
        "topic_preferences": {
            "ai": 0.22,
            "backend": 0.59,
            "system-design": 0.76,
            "devops": 0.94,
            "interview-prep": 0.28,
        },
    },
    {
        "username": "dana_ml",
        "email": "dana@example.com",
        "bio": "Applied ML practitioner following LLM workflows, evaluation, and model serving patterns.",
        "topic_preferences": {
            "ai": 0.97,
            "backend": 0.41,
            "system-design": 0.52,
            "devops": 0.33,
            "interview-prep": 0.61,
        },
    },
    {
        "username": "emma_fullstack",
        "email": "emma@example.com",
        "bio": "Full-stack builder preparing for interviews while keeping up with backend and AI trends.",
        "topic_preferences": {
            "ai": 0.56,
            "backend": 0.79,
            "system-design": 0.63,
            "devops": 0.48,
            "interview-prep": 0.88,
        },
    },
]


async def seed_users() -> None:
    """Seed demo users into the database."""

    print_step("USERS", "Connecting to database...")
    async_session, engine = await get_async_session()

    try:
        async with async_session() as session:
            existing_usernames = set(
                (
                    await session.execute(
                        select(User.username).where(
                            User.username.in_([user["username"] for user in DEMO_USERS])
                        )
                    )
                )
                .scalars()
                .all()
            )

            created_count = 0
            skipped_count = 0

            print_step("USERS", "Ensuring demo users exist...")
            for user_data in DEMO_USERS:
                if user_data["username"] in existing_usernames:
                    skipped_count += 1
                    print(f"  ↷ Skipped existing user: {user_data['username']}")
                    continue

                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                )
                session.add(user)
                await session.flush()

                session.add(
                    UserProfile(
                        user_id=user.id,
                        bio=user_data["bio"],
                        topic_preferences=user_data["topic_preferences"],
                    )
                )
                created_count += 1
                print(f"  → Created user: {user_data['username']} ({user_data['email']})")

            await session.commit()
            print_step(
                "USERS",
                f"Created {created_count} demo users, skipped {skipped_count} existing users",
            )
    except Exception as e:
        print_error(f"Failed to seed users: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_users())
    print_success("User seeding completed")
