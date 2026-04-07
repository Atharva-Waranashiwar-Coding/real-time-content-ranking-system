"""Seed script for demo users."""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import select
from seed_utils import get_async_session, print_step, print_error, print_success

# Add user-service to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "user-service"))

from app.models import User, UserProfile


# Demo user data
DEMO_USERS = [
    {
        "username": "alice_dev",
        "email": "alice@example.com",
        "topic_preferences": {"ai": 0.9, "backend": 0.6, "system-design": 0.7},
    },
    {
        "username": "bob_engineer",
        "email": "bob@example.com",
        "topic_preferences": {"backend": 0.95, "system-design": 0.8, "devops": 0.5},
    },
    {
        "username": "charlie_sysadmin",
        "email": "charlie@example.com",
        "topic_preferences": {"devops": 0.9, "system-design": 0.7, "backend": 0.6},
    },
    {
        "username": "dana_ml",
        "email": "dana@example.com",
        "topic_preferences": {"ai": 0.95, "backend": 0.4, "interview-prep": 0.6},
    },
    {
        "username": "emma_fullstack",
        "email": "emma@example.com",
        "topic_preferences": {"backend": 0.7, "ai": 0.5, "interview-prep": 0.8},
    },
]


async def seed_users():
    """Seed demo users into the database."""
    print_step("USERS", "Connecting to database...")
    async_session, engine = await get_async_session()
    
    try:
        async with async_session() as session:
            # Check if users already exist
            query = select(User)
            result = await session.execute(query)
            existing_users = result.scalars().all()
            
            if existing_users:
                print_step("USERS", f"Found {len(existing_users)} existing users. Skipping user creation.")
                return
            
            print_step("USERS", "Creating demo users...")
            
            created_count = 0
            for user_data in DEMO_USERS:
                try:
                    # Create user
                    user = User(
                        username=user_data["username"],
                        email=user_data["email"],
                    )
                    session.add(user)
                    await session.flush()
                    
                    # Create profile
                    profile = UserProfile(
                        user_id=user.id,
                        bio=f"Demo user for {user_data['username']}",
                        topic_preferences=user_data["topic_preferences"],
                    )
                    session.add(profile)
                    
                    created_count += 1
                    print(f"  → Created user: {user_data['username']} ({user_data['email']})")
                except Exception as e:
                    print(f"  ! Failed to create user {user_data['username']}: {e}")
            
            await session.commit()
            print_step("USERS", f"Successfully created {created_count} demo users")
            
    except Exception as e:
        print_error(f"Failed to seed users: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_users())
    print_success("User seeding completed")
