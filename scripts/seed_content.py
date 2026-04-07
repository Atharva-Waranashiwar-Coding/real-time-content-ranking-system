"""Seed script for demo content items."""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from seed_utils import get_async_session, print_error, print_step, print_success
from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "content-service"))

from app.models import ContentItem, ContentTag

from shared_schemas import ContentCategory, ContentStatus

DEMO_TAGS = {
    "ai": "Artificial intelligence and machine learning topics",
    "llm": "Large language model patterns and workflows",
    "backend": "Backend engineering practices",
    "system-design": "Architecture and distributed systems concepts",
    "devops": "Operations, deployment, and platform engineering",
    "interview-prep": "Interview preparation content",
    "databases": "Database design and performance topics",
    "distributed-systems": "Distributed systems and scalability concepts",
    "api-design": "API design, contracts, and integrations",
    "kubernetes": "Kubernetes and container orchestration",
}

DEMO_CONTENT = {
    ContentCategory.AI: [
        {"title": "Understanding Large Language Models", "description": "Deep dive into how LLMs work", "topic": "ai"},
        {"title": "Embeddings and Vector Databases", "description": "Using embeddings for semantic search", "topic": "ai"},
        {"title": "Prompt Engineering Best Practices", "description": "Techniques for better LLM outputs", "topic": "ai"},
        {"title": "Retrieval Augmented Generation (RAG)", "description": "Combining LLMs with external knowledge", "topic": "ai"},
        {"title": "Fine-tuning Transformers", "description": "Adapting pre-trained models", "topic": "ai"},
        {"title": "Building AI Agents", "description": "Creating autonomous AI systems", "topic": "ai"},
        {"title": "Attention Mechanisms Explained", "description": "Core concept behind transformers", "topic": "ai"},
        {"title": "Computer Vision Fundamentals", "description": "Image processing and neural networks", "topic": "ai"},
        {"title": "NLP Pipeline Design", "description": "From raw text to predictions", "topic": "ai"},
        {"title": "Ethical AI and Bias Mitigation", "description": "Building responsible AI systems", "topic": "ai"},
        {"title": "Reinforcement Learning Basics", "description": "Learning through rewards and penalties", "topic": "ai"},
        {"title": "Model Evaluation and Metrics", "description": "Measuring AI model performance", "topic": "ai"},
    ],
    ContentCategory.BACKEND: [
        {"title": "REST API Design Patterns", "description": "Building scalable HTTP APIs", "topic": "backend"},
        {"title": "Database Normalization", "description": "Structuring relational databases", "topic": "backend"},
        {"title": "Caching Strategies", "description": "Improving application performance", "topic": "backend"},
        {"title": "Message Queues and Event Streaming", "description": "Asynchronous communication", "topic": "backend"},
        {"title": "ORM vs Raw SQL", "description": "Choosing the right data access pattern", "topic": "backend"},
        {"title": "Microservices Architecture", "description": "Building distributed backend systems", "topic": "backend"},
        {"title": "API Authentication and Authorization", "description": "Securing your APIs", "topic": "backend"},
        {"title": "Database Indexing", "description": "Optimizing query performance", "topic": "backend"},
        {"title": "Rate Limiting and Throttling", "description": "Protecting your backend", "topic": "backend"},
        {"title": "GraphQL vs REST", "description": "Query patterns for APIs", "topic": "backend"},
        {"title": "Transaction Management", "description": "ACID properties in databases", "topic": "backend"},
        {"title": "Connection Pooling", "description": "Managing database connections", "topic": "backend"},
    ],
    ContentCategory.SYSTEM_DESIGN: [
        {"title": "Scalability Fundamentals", "description": "Designing systems that grow", "topic": "system-design"},
        {"title": "CAP Theorem Explained", "description": "Trade-offs in distributed systems", "topic": "system-design"},
        {"title": "Load Balancing Strategies", "description": "Distributing traffic effectively", "topic": "system-design"},
        {"title": "Consistent Hashing", "description": "Scalable data distribution", "topic": "system-design"},
        {"title": "Sharding and Partitioning", "description": "Horizontal data scaling", "topic": "system-design"},
        {"title": "Replication and Redundancy", "description": "Ensuring high availability", "topic": "system-design"},
        {"title": "System Design Interview Guide", "description": "Preparing for system design questions", "topic": "system-design"},
        {"title": "Latency and Throughput", "description": "Understanding performance metrics", "topic": "system-design"},
        {"title": "Rate Limiting in Distributed Apps", "description": "Managing resource constraints", "topic": "system-design"},
        {"title": "Data Center Design", "description": "Physical infrastructure considerations", "topic": "system-design"},
        {"title": "Service Discovery", "description": "Managing dynamic service locations", "topic": "system-design"},
    ],
    ContentCategory.DEVOPS: [
        {"title": "CI/CD Pipeline Design", "description": "Automating software delivery", "topic": "devops"},
        {"title": "Kubernetes Basics", "description": "Container orchestration essentials", "topic": "devops"},
        {"title": "Docker Best Practices", "description": "Containerizing applications", "topic": "devops"},
        {"title": "Infrastructure as Code", "description": "Managing infrastructure with code", "topic": "devops"},
        {"title": "Monitoring and Observability", "description": "Understanding production systems", "topic": "devops"},
        {"title": "Log Aggregation", "description": "Centralizing application logs", "topic": "devops"},
        {"title": "GitOps Workflow", "description": "Git-driven deployment strategy", "topic": "devops"},
        {"title": "Blue-Green Deployments", "description": "Zero-downtime updates", "topic": "devops"},
        {"title": "Disaster Recovery Planning", "description": "Business continuity strategies", "topic": "devops"},
        {"title": "Security Best Practices", "description": "DevSecOps fundamentals", "topic": "devops"},
    ],
    ContentCategory.INTERVIEW_PREP: [
        {"title": "Coding Interview Patterns", "description": "Common problem-solving approaches", "topic": "interview-prep"},
        {"title": "System Design Interview", "description": "Designing large-scale systems", "topic": "interview-prep"},
        {"title": "Behavioral Interview Preparation", "description": "Acing the soft skills interview", "topic": "interview-prep"},
        {"title": "Data Structure Cheat Sheet", "description": "Quick reference for interviews", "topic": "interview-prep"},
        {"title": "Algorithm Analysis", "description": "Big O complexity explained", "topic": "interview-prep"},
        {"title": "Mock Interview Tips", "description": "Practicing for the real thing", "topic": "interview-prep"},
    ],
}

CATEGORY_DEFAULT_TAGS = {
    ContentCategory.AI: ["ai", "llm"],
    ContentCategory.BACKEND: ["backend", "api-design"],
    ContentCategory.SYSTEM_DESIGN: ["system-design", "distributed-systems"],
    ContentCategory.DEVOPS: ["devops", "kubernetes"],
    ContentCategory.INTERVIEW_PREP: ["interview-prep", "system-design"],
}

KEYWORD_TAGS = {
    "database": "databases",
    "databases": "databases",
    "sql": "databases",
    "api": "api-design",
    "graphql": "api-design",
    "distributed": "distributed-systems",
    "scalability": "distributed-systems",
    "kubernetes": "kubernetes",
    "docker": "kubernetes",
    "llm": "llm",
    "transformer": "llm",
}


def build_tag_names(category: ContentCategory, title: str) -> list[str]:
    """Build a deterministic tag list for a content item."""

    tag_names = list(CATEGORY_DEFAULT_TAGS[category])
    lower_title = title.lower()
    for keyword, tag_name in KEYWORD_TAGS.items():
        if keyword in lower_title and tag_name not in tag_names:
            tag_names.append(tag_name)
    return tag_names


def build_status(index: int) -> ContentStatus:
    """Create a deterministic mix of drafts and published items."""

    return ContentStatus.DRAFT if index % 8 == 0 else ContentStatus.PUBLISHED


def build_engagement_metadata(index: int, status: ContentStatus) -> dict[str, int]:
    """Create repeatable engagement counters for seeded content."""

    if status == ContentStatus.DRAFT:
        return {"impressions": 0, "clicks": 0, "likes": 0, "saves": 0, "skips": 0}

    impressions = 140 + (index * 17)
    clicks = 28 + (index * 4)
    likes = 9 + (index % 11)
    saves = 4 + (index % 7)
    skips = 3 + (index % 5)
    return {
        "impressions": impressions,
        "clicks": clicks,
        "likes": likes,
        "saves": saves,
        "skips": skips,
    }


async def seed_content() -> None:
    """Seed demo content items into the database."""

    print_step("CONTENT", "Connecting to database...")
    async_session, engine = await get_async_session()

    try:
        async with async_session() as session:
            existing_tags = {
                tag.name: tag
                for tag in (
                    await session.execute(
                        select(ContentTag).where(ContentTag.name.in_(DEMO_TAGS.keys()))
                    )
                )
                .scalars()
                .all()
            }

            created_tags = 0
            for tag_name, description in DEMO_TAGS.items():
                if tag_name in existing_tags:
                    continue

                tag = ContentTag(name=tag_name, description=description)
                session.add(tag)
                await session.flush()
                existing_tags[tag.name] = tag
                created_tags += 1

            existing_titles = set(
                (
                    await session.execute(
                        select(ContentItem.title).where(
                            ContentItem.title.in_(
                                [
                                    item["title"]
                                    for items in DEMO_CONTENT.values()
                                    for item in items
                                ]
                            )
                        )
                    )
                )
                .scalars()
                .all()
            )

            created_count = 0
            skipped_count = 0
            seeded_index = 0
            now = datetime.now(timezone.utc)

            print_step("CONTENT", "Ensuring demo tags and content items exist...")
            for category, items in DEMO_CONTENT.items():
                print(f"  → Processing {len(items)} items in '{category.value}'")
                for item_data in items:
                    if item_data["title"] in existing_titles:
                        skipped_count += 1
                        print(f"    ↷ Skipped existing content: {item_data['title']}")
                        seeded_index += 1
                        continue

                    status = build_status(seeded_index)
                    engagement_metadata = build_engagement_metadata(seeded_index, status)
                    published_at = (
                        now - timedelta(days=(seeded_index % 18) + 1)
                        if status == ContentStatus.PUBLISHED
                        else None
                    )

                    content = ContentItem(
                        title=item_data["title"],
                        description=item_data["description"],
                        topic=item_data["topic"],
                        category=category.value,
                        status=status.value,
                        published_at=published_at,
                        view_count=engagement_metadata["clicks"] * 3,
                        engagement_metadata=engagement_metadata,
                    )
                    content.tags = [
                        existing_tags[tag_name]
                        for tag_name in build_tag_names(category, item_data["title"])
                    ]

                    session.add(content)
                    created_count += 1
                    seeded_index += 1
                    print(
                        f"    → Created {status.value} content: {item_data['title']} "
                        f"[{', '.join(tag.name for tag in content.tags)}]"
                    )

            await session.commit()
            print_step(
                "CONTENT",
                f"Created {created_count} content items and {created_tags} tags, "
                f"skipped {skipped_count} existing content items",
            )

            print("\n  Summary by category:")
            for category, items in DEMO_CONTENT.items():
                print(f"    - {category.value}: {len(items)} items")
    except Exception as e:
        print_error(f"Failed to seed content: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_content())
    print_success("Content seeding completed")
