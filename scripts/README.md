# Seed Scripts Documentation

This directory contains seed scripts for populating demo data into the system.

## Overview

The seed scripts provide deterministic demo data for development and testing:
- **5 demo users** with topic preferences
- **50+ tech learning content items** across 5 categories

## Usage

### Prerequisites

1. Ensure Docker Compose stack is running:
   ```bash
   docker-compose -f infra/docker/docker-compose.yml up -d
   ```

2. Run initial migrations:
   ```bash
   # User service migrations
   cd services/user-service
   alembic upgrade head

   # Content service migrations
   cd services/content-service
   alembic upgrade head
   ```

### Seeding Data

```bash
# Install script dependencies
pip install -r scripts/requirements.txt

# Seed users
python scripts/seed_users.py

# Seed content items
python scripts/seed_content.py

# Run both (from project root)
python scripts/seed_users.py && python scripts/seed_content.py
```

## Demo Data Details

### Users

| Username | Email | Topics |
|----------|-------|--------|
| alice_dev | alice@example.com | AI (0.9), Backend (0.6), System Design (0.7) |
| bob_engineer | bob@example.com | Backend (0.95), System Design (0.8), DevOps (0.5) |
| charlie_sysadmin | charlie@example.com | DevOps (0.9), System Design (0.7), Backend (0.6) |
| dana_ml | dana@example.com | AI (0.95), Backend (0.4), Interview Prep (0.6) |
| emma_fullstack | emma@example.com | Backend (0.7), AI (0.5), Interview Prep (0.8) |

### Content Categories

- **AI** (12 items): LLMs, embeddings, prompt engineering, RAG, transformers, etc.
- **Backend** (12 items): REST APIs, databases, caching, messaging, microservices, etc.
- **System Design** (11 items): Scalability, CAP theorem, consistency, load balancing, etc.
- **DevOps** (9 items): CI/CD, Kubernetes, Docker, infrastructure as code, monitoring, etc.
- **Interview Prep** (6 items): Coding patterns, system design, behavioral prep, etc.

## Idempotency

The seed scripts are idempotent:
- If data already exists, scripts will skip creation
- Safe to run multiple times
- Useful for resetting specific data without full database wipe

## Configuration

Scripts read from environment variables:

```env
DB_HOST=localhost        # Database host (default: localhost)
DB_PORT=5432            # Database port (default: 5432)
DB_USER=rankinguser      # Database user
DB_PASSWORD=rankingpass  # Database password
DB_NAME=ranking_db       # Database name
```

Or from `.env` file in project root.

## Future Enhancements

- Add seed data for interactions
- Create scripted user session scenarios
- Add feature flags for conditional seeding
- Support seed data cleanup/reset
