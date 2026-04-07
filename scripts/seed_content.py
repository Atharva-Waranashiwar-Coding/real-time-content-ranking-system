"""Seed script for demo content items."""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import select
from seed_utils import get_async_session, print_step, print_error, print_success

# Add content-service to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "content-service"))

from app.models import ContentItem, ContentTag
from shared_schemas import ContentCategory, ContentStatus


# Demo content items across categories
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


async def seed_content():
    """Seed demo content items into the database."""
    print_step("CONTENT", "Connecting to database...")
    async_session, engine = await get_async_session()
    
    try:
        async with async_session() as session:
            # Check if content already exists
            query = select(ContentItem)
            result = await session.execute(query)
            existing_content = result.scalars().all()
            
            if existing_content:
                print_step("CONTENT", f"Found {len(existing_content)} existing content items. Skipping creation.")
                return
            
            print_step("CONTENT", "Creating demo content items...")
            
            created_count = 0
            for category, items in DEMO_CONTENT.items():
                print(f"  → Creating {len(items)} items in '{category.value}' category")
                
                for item_data in items:
                    try:
                        content = ContentItem(
                            title=item_data["title"],
                            description=item_data["description"],
                            topic=item_data["topic"],
                            category=category.value,
                            status="published",
                            engagement_metadata={
                                "impressions": 0,
                                "clicks": 0,
                                "likes": 0,
                                "saves": 0,
                                "skips": 0,
                            },
                        )
                        session.add(content)
                        created_count += 1
                    except Exception as e:
                        print(f"    ! Failed to create content item: {e}")
            
            await session.commit()
            print_step("CONTENT", f"Successfully created {created_count} demo content items")
            
            # Print summary by category
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
