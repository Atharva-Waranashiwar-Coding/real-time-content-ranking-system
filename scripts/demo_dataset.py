"""Canonical deterministic dataset for demos, seeds, and documentation."""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timedelta, timezone

DEMO_DEFAULT_USERNAME = "alice_dev"
DEMO_EXPERIMENT_KEY = "home_feed_ranking.v1"
DEMO_REFERENCE_TIME_ENV = "DEMO_REFERENCE_TIME"
DEMO_DEFAULT_REFERENCE_TIME = "2026-04-08T14:00:00+00:00"

CONTROL_VARIANT_KEY = "control"
TRENDING_BOOST_VARIANT_KEY = "trending_boost"
RULES_V1_STRATEGY = "rules_v1"
RULES_V2_STRATEGY = "rules_v2_with_trending_boost"

TOPIC_ORDER = (
    "ai",
    "backend",
    "system-design",
    "devops",
    "interview-prep",
)

DEMO_USERS = [
    {
        "id": "10000000-0000-0000-0000-000000000001",
        "profile_id": "11000000-0000-0000-0000-000000000001",
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
        "id": "10000000-0000-0000-0000-000000000002",
        "profile_id": "11000000-0000-0000-0000-000000000002",
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
        "id": "10000000-0000-0000-0000-000000000003",
        "profile_id": "11000000-0000-0000-0000-000000000003",
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
        "id": "10000000-0000-0000-0000-000000000004",
        "profile_id": "11000000-0000-0000-0000-000000000004",
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
        "id": "10000000-0000-0000-0000-000000000005",
        "profile_id": "11000000-0000-0000-0000-000000000005",
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

DEMO_TAGS = [
    {
        "id": "30000000-0000-0000-0000-000000000001",
        "name": "ai",
        "description": "Artificial intelligence and machine learning topics",
    },
    {
        "id": "30000000-0000-0000-0000-000000000002",
        "name": "llm",
        "description": "Large language model patterns and workflows",
    },
    {
        "id": "30000000-0000-0000-0000-000000000003",
        "name": "backend",
        "description": "Backend engineering practices",
    },
    {
        "id": "30000000-0000-0000-0000-000000000004",
        "name": "system-design",
        "description": "Architecture and distributed systems concepts",
    },
    {
        "id": "30000000-0000-0000-0000-000000000005",
        "name": "devops",
        "description": "Operations, deployment, and platform engineering",
    },
    {
        "id": "30000000-0000-0000-0000-000000000006",
        "name": "interview-prep",
        "description": "Interview preparation content",
    },
    {
        "id": "30000000-0000-0000-0000-000000000007",
        "name": "databases",
        "description": "Database design and performance topics",
    },
    {
        "id": "30000000-0000-0000-0000-000000000008",
        "name": "distributed-systems",
        "description": "Distributed systems and scalability concepts",
    },
    {
        "id": "30000000-0000-0000-0000-000000000009",
        "name": "api-design",
        "description": "API design, contracts, and integrations",
    },
    {
        "id": "30000000-0000-0000-0000-000000000010",
        "name": "kubernetes",
        "description": "Kubernetes and container orchestration",
    },
]

CONTENT_BLUEPRINTS = {
    "ai": [
        ("Understanding Large Language Models", "Deep dive into how LLMs work", "ai"),
        ("Embeddings and Vector Databases", "Using embeddings for semantic search", "ai"),
        ("Prompt Engineering Best Practices", "Techniques for better LLM outputs", "ai"),
        ("Retrieval Augmented Generation (RAG)", "Combining LLMs with external knowledge", "ai"),
        ("Fine-tuning Transformers", "Adapting pre-trained models", "ai"),
        ("Building AI Agents", "Creating autonomous AI systems", "ai"),
        ("Attention Mechanisms Explained", "Core concept behind transformers", "ai"),
        ("Computer Vision Fundamentals", "Image processing and neural networks", "ai"),
        ("NLP Pipeline Design", "From raw text to predictions", "ai"),
        ("Ethical AI and Bias Mitigation", "Building responsible AI systems", "ai"),
        ("Reinforcement Learning Basics", "Learning through rewards and penalties", "ai"),
        ("Model Evaluation and Metrics", "Measuring AI model performance", "ai"),
    ],
    "backend": [
        ("REST API Design Patterns", "Building scalable HTTP APIs", "backend"),
        ("Database Normalization", "Structuring relational databases", "backend"),
        ("Caching Strategies", "Improving application performance", "backend"),
        ("Message Queues and Event Streaming", "Asynchronous communication", "backend"),
        ("ORM vs Raw SQL", "Choosing the right data access pattern", "backend"),
        ("Microservices Architecture", "Building distributed backend systems", "backend"),
        ("API Authentication and Authorization", "Securing your APIs", "backend"),
        ("Database Indexing", "Optimizing query performance", "backend"),
        ("Rate Limiting and Throttling", "Protecting your backend", "backend"),
        ("GraphQL vs REST", "Query patterns for APIs", "backend"),
        ("Transaction Management", "ACID properties in databases", "backend"),
        ("Connection Pooling", "Managing database connections", "backend"),
    ],
    "system-design": [
        ("Scalability Fundamentals", "Designing systems that grow", "system-design"),
        ("CAP Theorem Explained", "Trade-offs in distributed systems", "system-design"),
        ("Load Balancing Strategies", "Distributing traffic effectively", "system-design"),
        ("Consistent Hashing", "Scalable data distribution", "system-design"),
        ("Sharding and Partitioning", "Horizontal data scaling", "system-design"),
        ("Replication and Redundancy", "Ensuring high availability", "system-design"),
        ("System Design Interview Guide", "Preparing for system design questions", "system-design"),
        ("Latency and Throughput", "Understanding performance metrics", "system-design"),
        ("Rate Limiting in Distributed Apps", "Managing resource constraints", "system-design"),
        ("Data Center Design", "Physical infrastructure considerations", "system-design"),
        ("Service Discovery", "Managing dynamic service locations", "system-design"),
    ],
    "devops": [
        ("CI/CD Pipeline Design", "Automating software delivery", "devops"),
        ("Kubernetes Basics", "Container orchestration essentials", "devops"),
        ("Docker Best Practices", "Containerizing applications", "devops"),
        ("Infrastructure as Code", "Managing infrastructure with code", "devops"),
        ("Monitoring and Observability", "Understanding production systems", "devops"),
        ("Log Aggregation", "Centralizing application logs", "devops"),
        ("GitOps Workflow", "Git-driven deployment strategy", "devops"),
        ("Blue-Green Deployments", "Zero-downtime updates", "devops"),
        ("Disaster Recovery Planning", "Business continuity strategies", "devops"),
        ("Security Best Practices", "DevSecOps fundamentals", "devops"),
    ],
    "interview-prep": [
        ("Coding Interview Patterns", "Common problem-solving approaches", "interview-prep"),
        ("System Design Interview", "Designing large-scale systems", "interview-prep"),
        ("Behavioral Interview Preparation", "Acing the soft skills interview", "interview-prep"),
        ("Data Structure Cheat Sheet", "Quick reference for interviews", "interview-prep"),
        ("Algorithm Analysis", "Big O complexity explained", "interview-prep"),
        ("Mock Interview Tips", "Practicing for the real thing", "interview-prep"),
    ],
}

CATEGORY_DEFAULT_TAGS = {
    "ai": ["ai", "llm"],
    "backend": ["backend", "api-design"],
    "system-design": ["system-design", "distributed-systems"],
    "devops": ["devops", "kubernetes"],
    "interview-prep": ["interview-prep", "system-design"],
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

HERO_CONTENT_PROFILES = {
    "Retrieval Augmented Generation (RAG)": {
        "impressions": 680,
        "clicks": 214,
        "likes": 66,
        "saves": 58,
        "skip_count": 19,
        "watch_starts": 166,
        "watch_completes": 113,
        "trending_score": 34.2,
    },
    "Building AI Agents": {
        "impressions": 640,
        "clicks": 205,
        "likes": 61,
        "saves": 44,
        "skip_count": 21,
        "watch_starts": 159,
        "watch_completes": 104,
        "trending_score": 32.8,
    },
    "Message Queues and Event Streaming": {
        "impressions": 620,
        "clicks": 198,
        "likes": 54,
        "saves": 42,
        "skip_count": 18,
        "watch_starts": 136,
        "watch_completes": 91,
        "trending_score": 31.6,
    },
    "REST API Design Patterns": {
        "impressions": 610,
        "clicks": 187,
        "likes": 49,
        "saves": 38,
        "skip_count": 22,
        "watch_starts": 120,
        "watch_completes": 76,
        "trending_score": 29.7,
    },
    "Scalability Fundamentals": {
        "impressions": 630,
        "clicks": 194,
        "likes": 57,
        "saves": 41,
        "skip_count": 17,
        "watch_starts": 138,
        "watch_completes": 94,
        "trending_score": 30.9,
    },
    "System Design Interview Guide": {
        "impressions": 590,
        "clicks": 176,
        "likes": 47,
        "saves": 39,
        "skip_count": 23,
        "watch_starts": 128,
        "watch_completes": 86,
        "trending_score": 28.4,
    },
    "Monitoring and Observability": {
        "impressions": 600,
        "clicks": 183,
        "likes": 51,
        "saves": 36,
        "skip_count": 20,
        "watch_starts": 126,
        "watch_completes": 87,
        "trending_score": 28.9,
    },
    "Kubernetes Basics": {
        "impressions": 560,
        "clicks": 165,
        "likes": 43,
        "saves": 31,
        "skip_count": 18,
        "watch_starts": 112,
        "watch_completes": 71,
        "trending_score": 26.7,
    },
    "Coding Interview Patterns": {
        "impressions": 540,
        "clicks": 156,
        "likes": 42,
        "saves": 35,
        "skip_count": 16,
        "watch_starts": 97,
        "watch_completes": 62,
        "trending_score": 25.9,
    },
    "Mock Interview Tips": {
        "impressions": 515,
        "clicks": 149,
        "likes": 39,
        "saves": 33,
        "skip_count": 14,
        "watch_starts": 91,
        "watch_completes": 59,
        "trending_score": 24.8,
    },
}

DEMO_SCENARIOS = [
    {
        "name": "AI-first personalization",
        "username": "alice_dev",
        "expected_variant": CONTROL_VARIANT_KEY,
        "expected_topics": ["ai", "system-design", "backend"],
        "hero_titles": [
            "Retrieval Augmented Generation (RAG)",
            "Scalability Fundamentals",
            "Prompt Engineering Best Practices",
        ],
    },
    {
        "name": "Backend systems focus",
        "username": "bob_engineer",
        "expected_variant": CONTROL_VARIANT_KEY,
        "expected_topics": ["backend", "system-design", "devops"],
        "hero_titles": [
            "Message Queues and Event Streaming",
            "REST API Design Patterns",
            "Service Discovery",
        ],
    },
    {
        "name": "Platform and observability view",
        "username": "charlie_sysadmin",
        "expected_variant": CONTROL_VARIANT_KEY,
        "expected_topics": ["devops", "system-design", "backend"],
        "hero_titles": [
            "Monitoring and Observability",
            "Kubernetes Basics",
            "Load Balancing Strategies",
        ],
    },
    {
        "name": "Trending boost experiment lens",
        "username": "dana_ml",
        "expected_variant": TRENDING_BOOST_VARIANT_KEY,
        "expected_topics": ["ai", "interview-prep", "system-design"],
        "hero_titles": [
            "Building AI Agents",
            "Model Evaluation and Metrics",
            "System Design Interview Guide",
        ],
    },
    {
        "name": "Interview preparation blend",
        "username": "emma_fullstack",
        "expected_variant": TRENDING_BOOST_VARIANT_KEY,
        "expected_topics": ["interview-prep", "backend", "ai"],
        "hero_titles": [
            "Mock Interview Tips",
            "Coding Interview Patterns",
            "REST API Design Patterns",
        ],
    },
]


def resolve_demo_reference_time() -> datetime:
    """Return the timestamp used to anchor seeded demo data."""

    raw_value = os.getenv(DEMO_REFERENCE_TIME_ENV, DEMO_DEFAULT_REFERENCE_TIME).strip()
    normalized = raw_value.replace("Z", "+00:00")
    reference_time = datetime.fromisoformat(normalized)
    if reference_time.tzinfo is None or reference_time.tzinfo.utcoffset(reference_time) is None:
        return reference_time.replace(tzinfo=timezone.utc)
    return reference_time.astimezone(timezone.utc)


def build_tag_names(category: str, title: str) -> list[str]:
    """Return the deterministic tag set for a content item."""

    tag_names = list(CATEGORY_DEFAULT_TAGS[category])
    lower_title = title.lower()
    for keyword, tag_name in KEYWORD_TAGS.items():
        if keyword in lower_title and tag_name not in tag_names:
            tag_names.append(tag_name)
    return tag_names


def build_status(index: int) -> str:
    """Return the deterministic publication status for a content item."""

    return "draft" if index % 8 == 0 else "published"


def build_demo_content() -> list[dict[str, object]]:
    """Return canonical content records with fixed IDs and derived timestamps."""

    reference_time = resolve_demo_reference_time()
    items: list[dict[str, object]] = []
    item_index = 1

    for category, blueprints in CONTENT_BLUEPRINTS.items():
        for category_index, (title, description, topic) in enumerate(blueprints):
            status = build_status(item_index - 1)
            published_at = None
            created_at = reference_time - timedelta(hours=(item_index * 7) + 6)
            if status == "published":
                published_at = reference_time - timedelta(hours=(item_index * 4) + category_index)
                created_at = published_at - timedelta(hours=12)

            items.append(
                {
                    "id": f"20000000-0000-0000-0000-{item_index:012d}",
                    "title": title,
                    "description": description,
                    "topic": topic,
                    "category": category,
                    "status": status,
                    "created_at": created_at,
                    "published_at": published_at,
                    "updated_at": created_at + timedelta(minutes=30),
                    "tag_names": build_tag_names(category, title),
                }
            )
            item_index += 1

    return items


def build_content_engagement_metadata(content_item: dict[str, object], index: int) -> dict[str, int]:
    """Return stable engagement counters for the content-service seed."""

    if content_item["status"] != "published":
        return {"impressions": 0, "clicks": 0, "likes": 0, "saves": 0, "skips": 0}

    hero_profile = HERO_CONTENT_PROFILES.get(str(content_item["title"]))
    if hero_profile is not None:
        return {
            "impressions": hero_profile["impressions"],
            "clicks": hero_profile["clicks"],
            "likes": hero_profile["likes"],
            "saves": hero_profile["saves"],
            "skips": hero_profile["skip_count"],
        }

    category = str(content_item["category"])
    base_impressions = {
        "ai": 390,
        "backend": 360,
        "system-design": 375,
        "devops": 340,
        "interview-prep": 310,
    }[category]
    impressions = base_impressions + (index * 11)
    clicks = 88 + (index * 3)
    likes = 24 + (index % 10)
    saves = 16 + (index % 7)
    skips = 11 + (index % 5)
    return {
        "impressions": impressions,
        "clicks": clicks,
        "likes": likes,
        "saves": saves,
        "skips": skips,
    }


def _rate(numerator: int, denominator: int) -> float:
    """Return a rounded rate while guarding against divide-by-zero."""

    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def build_content_feature_rows() -> list[dict[str, object]]:
    """Return deterministic Redis and snapshot-ready content feature rows."""

    reference_time = resolve_demo_reference_time()
    rows: list[dict[str, object]] = []

    for index, content_item in enumerate(build_demo_content(), start=1):
        if content_item["status"] != "published":
            continue

        hero_profile = HERO_CONTENT_PROFILES.get(str(content_item["title"]))
        if hero_profile is None:
            category = str(content_item["category"])
            impressions = {
                "ai": 420,
                "backend": 395,
                "system-design": 405,
                "devops": 360,
                "interview-prep": 330,
            }[category] + (index * 9)
            clicks = 112 + (index * 2)
            likes = 31 + (index % 11)
            saves = 20 + (index % 8)
            skip_count = 12 + (index % 4)
            watch_starts = max(clicks - 24, 0)
            watch_completes = max(watch_starts - (14 + (index % 6)), 0)
            age_hours = max(
                int((reference_time - content_item["published_at"]).total_seconds() // 3600),
                1,
            )
            trending_score = round(
                17.0 + (index % 7) * 1.3 + max(0, 36 - age_hours) * 0.18,
                2,
            )
        else:
            impressions = hero_profile["impressions"]
            clicks = hero_profile["clicks"]
            likes = hero_profile["likes"]
            saves = hero_profile["saves"]
            skip_count = hero_profile["skip_count"]
            watch_starts = hero_profile["watch_starts"]
            watch_completes = hero_profile["watch_completes"]
            trending_score = hero_profile["trending_score"]

        rows.append(
            {
                "content_id": content_item["id"],
                "topic": content_item["topic"],
                "window_hours": 24,
                "impressions": impressions,
                "clicks": clicks,
                "likes": likes,
                "saves": saves,
                "skip_count": skip_count,
                "watch_starts": watch_starts,
                "watch_completes": watch_completes,
                "ctr": _rate(clicks, impressions),
                "like_rate": _rate(likes, impressions),
                "save_rate": _rate(saves, impressions),
                "skip_rate": _rate(skip_count, impressions),
                "completion_rate": _rate(watch_completes, watch_starts),
                "trending_score": trending_score,
                "last_event_at": reference_time - timedelta(minutes=index % 37),
                "updated_at": reference_time,
                "snapshot_at": reference_time,
            }
        )

    return rows


def build_user_topic_affinity_rows() -> list[dict[str, object]]:
    """Return deterministic Redis and snapshot-ready user affinity rows."""

    reference_time = resolve_demo_reference_time()
    rows: list[dict[str, object]] = []

    for user in DEMO_USERS:
        topic_preferences = user["topic_preferences"]
        for index, topic in enumerate(TOPIC_ORDER, start=1):
            preference = float(topic_preferences.get(topic, 0.0))
            affinity_score = round((preference * 10.0) + index * 0.15, 4)
            impressions = 12 + int(preference * 20)
            clicks = max(1, int(preference * 10))
            likes = max(0, int(preference * 7))
            saves = max(0, int(preference * 5))
            skip_count = max(0, 4 - int(preference * 3))
            watch_starts = max(1, int(preference * 9))
            watch_completes = max(0, int(preference * 6))
            rows.append(
                {
                    "user_id": user["id"],
                    "topic": topic,
                    "window_hours": 24,
                    "impressions": impressions,
                    "clicks": clicks,
                    "likes": likes,
                    "saves": saves,
                    "skip_count": skip_count,
                    "watch_starts": watch_starts,
                    "watch_completes": watch_completes,
                    "affinity_score": affinity_score,
                    "last_event_at": reference_time - timedelta(minutes=index * 3),
                    "updated_at": reference_time,
                    "snapshot_at": reference_time,
                }
            )

    return rows


def compute_assignment(user_id: str) -> dict[str, object]:
    """Return the deterministic experiment assignment for a user ID."""

    digest = hashlib.sha256(f"{DEMO_EXPERIMENT_KEY}:{user_id}".encode()).digest()
    assignment_bucket = int.from_bytes(digest[:8], byteorder="big") % 10000
    if assignment_bucket < 5000:
        variant_key = CONTROL_VARIANT_KEY
        strategy_name = RULES_V1_STRATEGY
    else:
        variant_key = TRENDING_BOOST_VARIANT_KEY
        strategy_name = RULES_V2_STRATEGY

    return {
        "experiment_key": DEMO_EXPERIMENT_KEY,
        "user_id": user_id,
        "assignment_bucket": assignment_bucket,
        "variant_key": variant_key,
        "strategy_name": strategy_name,
    }


def build_experiment_assignments() -> list[dict[str, object]]:
    """Return deterministic persisted experiment assignments for demo users."""

    reference_time = resolve_demo_reference_time()
    assignments: list[dict[str, object]] = []

    for index, user in enumerate(DEMO_USERS, start=1):
        assignment = compute_assignment(str(user["id"]))
        assignments.append(
            {
                "id": f"40000000-0000-0000-0000-{index:012d}",
                "schema_name": "experiment_assignment.v1",
                "experiment_key": assignment["experiment_key"],
                "variant_key": assignment["variant_key"],
                "strategy_name": assignment["strategy_name"],
                "user_id": assignment["user_id"],
                "assignment_bucket": assignment["assignment_bucket"],
                "assigned_at": reference_time - timedelta(hours=6),
                "updated_at": reference_time - timedelta(hours=6),
            }
        )

    return assignments


def build_experiment_exposures() -> list[dict[str, object]]:
    """Return deterministic exposure rows and attributed demo interactions."""

    reference_time = resolve_demo_reference_time()
    content_by_title = {item["title"]: item for item in build_demo_content()}
    user_by_username = {user["username"]: user for user in DEMO_USERS}

    exposure_blueprints = [
        ("alice_dev", 1, ["Retrieval Augmented Generation (RAG)", "Scalability Fundamentals", "Prompt Engineering Best Practices", "Message Queues and Event Streaming"], {"click": [1], "save": [1], "watch_complete": [1]}),
        ("bob_engineer", 2, ["Message Queues and Event Streaming", "REST API Design Patterns", "Service Discovery", "Scalability Fundamentals"], {"click": [1, 2], "save": [2], "watch_complete": []}),
        ("charlie_sysadmin", 3, ["Monitoring and Observability", "Kubernetes Basics", "Load Balancing Strategies", "CI/CD Pipeline Design"], {"click": [1], "save": [1], "watch_complete": [1]}),
        ("dana_ml", 4, ["Building AI Agents", "Model Evaluation and Metrics", "System Design Interview Guide", "Retrieval Augmented Generation (RAG)"], {"click": [1, 2], "save": [], "watch_complete": [1, 2]}),
        ("emma_fullstack", 5, ["Mock Interview Tips", "Coding Interview Patterns", "REST API Design Patterns", "Behavioral Interview Preparation"], {"click": [1, 2], "save": [1], "watch_complete": [1, 2]}),
    ]

    exposures: list[dict[str, object]] = []
    interaction_index = 1

    for exposure_index, (username, hour_offset, titles, outcomes) in enumerate(
        exposure_blueprints,
        start=1,
    ):
        user = user_by_username[username]
        assignment = compute_assignment(str(user["id"]))
        generated_at = reference_time - timedelta(hours=hour_offset)
        items: list[dict[str, object]] = []
        interactions: list[dict[str, object]] = []

        for rank, title in enumerate(titles, start=1):
            content_item = content_by_title[title]
            item_id = f"42000000-0000-0000-0000-{(exposure_index * 10) + rank:012d}"
            items.append(
                {
                    "id": item_id,
                    "content_id": content_item["id"],
                    "rank": rank,
                    "score": round(0.84 - (rank * 0.07) + exposure_index * 0.01, 6),
                    "topic": content_item["topic"],
                    "category": content_item["category"],
                    "created_at": generated_at,
                }
            )

            for event_type, item_ranks in outcomes.items():
                if rank not in item_ranks:
                    continue
                event_timestamp = generated_at + timedelta(minutes=(rank * 3) + interaction_index)
                watch_duration_seconds = 0
                if event_type == "watch_complete":
                    watch_duration_seconds = 180 + (rank * 12)
                interactions.append(
                    {
                        "id": f"50000000-0000-0000-0000-{interaction_index:012d}",
                        "event_id": f"51000000-0000-0000-0000-{interaction_index:012d}",
                        "event_type": event_type,
                        "user_id": user["id"],
                        "content_id": content_item["id"],
                        "session_id": f"demo-session-{username}",
                        "topic": content_item["topic"],
                        "watch_duration_seconds": watch_duration_seconds,
                        "request_id": f"req-demo-{interaction_index:04d}",
                        "correlation_id": f"corr-demo-{interaction_index:04d}",
                        "event_timestamp": event_timestamp,
                        "created_at": event_timestamp,
                        "published_at": event_timestamp + timedelta(seconds=1),
                    }
                )
                interaction_index += 1

        exposures.append(
            {
                "id": f"41000000-0000-0000-0000-{exposure_index:012d}",
                "schema_name": "experiment_exposure.v1",
                "experiment_key": assignment["experiment_key"],
                "variant_key": assignment["variant_key"],
                "strategy_name": assignment["strategy_name"],
                "user_id": user["id"],
                "session_id": f"demo-session-{username}",
                "request_id": f"req-exposure-{exposure_index:04d}",
                "correlation_id": f"corr-exposure-{exposure_index:04d}",
                "feed_limit": len(titles),
                "feed_offset": 0,
                "cache_hit": False,
                "generated_at": generated_at,
                "created_at": generated_at,
                "items": items,
                "interactions": interactions,
            }
        )

    return exposures

