"""Seed script for deterministic demo users."""

import asyncio
import sys
from datetime import timedelta
from pathlib import Path

from demo_dataset import DEMO_USERS, resolve_demo_reference_time
from seed_utils import get_async_session, print_error, print_step, print_success
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "user-service"))

from app.models import User, UserProfile


async def seed_users() -> None:
    """Seed demo users into the database."""

    print_step("USERS", "Connecting to database...")
    async_session, engine = await get_async_session()
    reference_time = resolve_demo_reference_time()

    try:
        async with async_session() as session:
            existing_users = {
                user.username: user
                for user in (
                    await session.execute(
                        select(User).where(
                            User.username.in_([user["username"] for user in DEMO_USERS])
                        )
                    )
                )
                .scalars()
                .all()
            }
            existing_profiles = {
                profile.user_id: profile
                for profile in (
                    await session.execute(
                        select(UserProfile).where(
                            UserProfile.user_id.in_([user["id"] for user in DEMO_USERS])
                        )
                    )
                )
                .scalars()
                .all()
            }

            created_count = 0
            skipped_count = 0

            print_step("USERS", "Ensuring demo users exist...")
            for index, user_data in enumerate(DEMO_USERS, start=1):
                existing_user = existing_users.get(user_data["username"])
                if existing_user is not None:
                    if existing_user.id != user_data["id"]:
                        raise RuntimeError(
                            "Found demo user with non-canonical ID for "
                            f"{user_data['username']}. Run scripts/reset_demo_state.py "
                            "before reseeding demo data."
                        )
                    existing_profile = existing_profiles.get(existing_user.id)
                    if existing_profile is None:
                        raise RuntimeError(
                            f"Demo profile missing for {user_data['username']}. "
                            "Run scripts/reset_demo_state.py before reseeding demo data."
                        )
                    skipped_count += 1
                    print(f"  ↷ Skipped existing user: {user_data['username']}")
                    continue

                user = User(
                    id=user_data["id"],
                    username=user_data["username"],
                    email=user_data["email"],
                    created_at=reference_time - timedelta(hours=index),
                    updated_at=reference_time,
                )
                session.add(user)
                session.add(
                    UserProfile(
                        id=user_data["profile_id"],
                        user_id=user_data["id"],
                        bio=user_data["bio"],
                        topic_preferences=user_data["topic_preferences"],
                        created_at=reference_time - timedelta(hours=index),
                        updated_at=reference_time,
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
