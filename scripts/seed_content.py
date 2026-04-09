"""Seed script for deterministic reference content items."""

import asyncio
import sys
from pathlib import Path

from demo_dataset import (
    DEMO_TAGS,
    build_content_engagement_metadata,
    build_demo_content,
    resolve_demo_reference_time,
)
from seed_utils import get_async_session, print_error, print_step, print_success
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "content-service"))

from app.models import ContentItem, ContentTag


async def seed_content() -> None:
    """Seed reference content items into the database."""

    print_step("CONTENT", "Connecting to database...")
    async_session, engine = await get_async_session()
    demo_content = build_demo_content()
    reference_time = resolve_demo_reference_time()

    try:
        async with async_session() as session:
            existing_tags = {
                tag.name: tag
                for tag in (
                    await session.execute(
                        select(ContentTag).where(
                            ContentTag.name.in_([tag["name"] for tag in DEMO_TAGS])
                        )
                    )
                )
                .scalars()
                .all()
            }

            created_tags = 0
            for tag_data in DEMO_TAGS:
                existing_tag = existing_tags.get(tag_data["name"])
                if existing_tag is not None:
                    if existing_tag.id != tag_data["id"]:
                        raise RuntimeError(
                            "Found seeded tag with non-canonical ID for "
                            f"{tag_data['name']}. Run scripts/reset_demo_state.py "
                            "before reseeding reference data."
                        )
                    continue

                tag = ContentTag(
                    id=tag_data["id"],
                    name=tag_data["name"],
                    description=tag_data["description"],
                    created_at=reference_time,
                    updated_at=reference_time,
                )
                session.add(tag)
                existing_tags[tag.name] = tag
                created_tags += 1

            titles = [item["title"] for item in demo_content]
            existing_titles = set(
                (
                    await session.execute(
                        select(ContentItem.title).where(
                            ContentItem.title.in_(titles)
                        )
                    )
                )
                .scalars()
                .all()
            )

            created_count = 0
            skipped_count = 0

            print_step("CONTENT", "Ensuring reference tags and content items exist...")
            category_counts: dict[str, int] = {}
            for index, item_data in enumerate(demo_content, start=1):
                category_counts[item_data["category"]] = (
                    category_counts.get(item_data["category"], 0) + 1
                )
                if item_data["title"] in existing_titles:
                    existing_item = (
                        (
                            await session.execute(
                                select(ContentItem).where(ContentItem.title == item_data["title"])
                            )
                        )
                        .scalars()
                        .first()
                    )
                    if existing_item is not None and existing_item.id != item_data["id"]:
                        raise RuntimeError(
                            "Found seeded content with non-canonical ID for "
                            f"{item_data['title']}. Run scripts/reset_demo_state.py "
                            "before reseeding reference data."
                        )
                    skipped_count += 1
                    print(f"  ↷ Skipped existing content: {item_data['title']}")
                    continue

                engagement_metadata = build_content_engagement_metadata(item_data, index)
                content = ContentItem(
                    id=item_data["id"],
                    title=item_data["title"],
                    description=item_data["description"],
                    topic=item_data["topic"],
                    category=item_data["category"],
                    status=item_data["status"],
                    created_at=item_data["created_at"],
                    published_at=item_data["published_at"],
                    updated_at=item_data["updated_at"],
                    view_count=engagement_metadata["clicks"] * 3,
                    engagement_metadata=engagement_metadata,
                )
                content.tags = [
                    existing_tags[tag_name]
                    for tag_name in item_data["tag_names"]
                ]

                session.add(content)
                created_count += 1
                print(
                    f"  → Created {item_data['status']} content: {item_data['title']} "
                    f"[{', '.join(tag.name for tag in content.tags)}]"
                )

            await session.commit()
            print_step(
                "CONTENT",
                f"Created {created_count} content items and {created_tags} tags, "
                f"skipped {skipped_count} existing content items",
            )

            print("\n  Summary by category:")
            for category, count in category_counts.items():
                print(f"    - {category}: {count} items")
    except Exception as e:
        print_error(f"Failed to seed content: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_content())
    print_success("Content seeding completed")
