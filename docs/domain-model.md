# Phase 1 Domain Model Documentation

## Entity Relationship Diagram

```
┌─────────────────────┐
│  users              │
├─────────────────────┤
│ id (PK)             │
│ username (UNIQUE)   │
│ email (UNIQUE)      │
│ created_at          │
│ updated_at          │
└─────────────────────┘
         │
         │ 1:1
         │
         ▼
┌─────────────────────────────┐
│  user_profiles              │
├─────────────────────────────┤
│ id (PK)                     │
│ user_id (FK, UNIQUE)        │
│ bio                         │
│ topic_preferences (JSON)    │
│ created_at                  │
│ updated_at                  │
└─────────────────────────────┘


┌──────────────────────┐
│  content_tags        │
├──────────────────────┤
│ id (PK)              │
│ name (UNIQUE)        │
│ description          │
│ created_at           │
│ updated_at           │
└──────────────────────┘
         │
         │ M:M
         │
         ▼
┌────────────────────────────────────┐
│  content_tags_association          │
├────────────────────────────────────┤
│ content_id (FK, PK part)           │
│ tag_id (FK, PK part)               │
└────────────────────────────────────┘
         ▲
         │ M:1
         │
         │
┌────────────────────────────────────┐
│  content_items                     │
├────────────────────────────────────┤
│ id (PK)                            │
│ title                              │
│ description                        │
│ topic                              │
│ category                           │
│ status (draft/published)           │
│ view_count                         │
│ engagement_metadata (JSON)         │
│ created_at                         │
│ published_at (nullable)            │
│ updated_at                         │
└────────────────────────────────────┘


┌────────────────────────────────────┐
│  interactions                      │
├────────────────────────────────────┤
│ id (PK)                            │
│ event_id (UNIQUE)                  │
│ schema_name                        │
│ event_type                         │
│ user_id                            │
│ content_id                         │
│ session_id                         │
│ topic                              │
│ watch_duration_seconds             │
│ metadata                           │
│ event_payload                      │
│ kafka_topic                        │
│ request_id                         │
│ correlation_id                     │
│ event_timestamp                    │
│ created_at                         │
│ published_at (nullable)            │
└────────────────────────────────────┘
```

## Core Entities

### User

Represents a user account in the system.

**Fields:**
- `id`: UUID (primary key)
- `username`: String, max 255, unique, indexed
- `email`: String, max 255, unique, indexed
- `created_at`: DateTime (UTC)
- `updated_at`: DateTime (UTC)

**Relationships:**
- 1:1 with UserProfile (cascade delete)

**Indexes:**
- username (unique)
- email (unique)
- created_at (for sorting)

### UserProfile

Extended user information and topic preferences for ranking.

**Fields:**
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key to User, unique)
- `bio`: String, max 500, nullable
- `topic_preferences`: JSON object with topic → score (0-1 range)
- `created_at`: DateTime (UTC)
- `updated_at`: DateTime (UTC)

**Relationships:**
- 1:1 with User

**Indexes:**
- user_id (unique)

**Example topic_preferences:**
```json
{
  "ai": 0.85,
  "backend": 0.6,
  "system-design": 0.75,
  "devops": 0.4,
  "interview-prep": 0.5
}
```

### ContentTag

Tag entity for organizing and categorizing content.

**Fields:**
- `id`: UUID (primary key)
- `name`: String, max 255, unique, indexed
- `description`: String, max 500, nullable
- `created_at`: DateTime (UTC)
- `updated_at`: DateTime (UTC)

**Relationships:**
- M:M with ContentItem (via content_tags_association)

**Indexes:**
- name (unique)

### ContentItem

Core content entity representing an article, tutorial, or resource.

**Fields:**
- `id`: UUID (primary key)
- `title`: String, max 500, indexed
- `description`: String, max 2000, nullable
- `topic`: String, max 100, indexed (e.g., "ai", "backend")
- `category`: String, max 50, indexed (enum: ai, backend, system-design, devops, interview-prep)
- `status`: String (enum: "draft" or "published"), indexed
- `view_count`: Integer, default 0
- `engagement_metadata`: JSON (stores impressions, likes, saves, etc.)
- `created_at`: DateTime (UTC), indexed
- `published_at`: DateTime (UTC), nullable, indexed
- `updated_at`: DateTime (UTC)

**Relationships:**
- M:M with ContentTag (via content_tags_association)

**Indexes:**
- title
- topic
- category
- status
- created_at
- published_at

**Content Categories:**
- `ai`: AI/ML related content
- `backend`: Backend engineering content
- `system-design`: System design and architecture
- `devops`: DevOps and infrastructure
- `interview-prep`: Interview preparation

**Example engagement_metadata:**
```json
{
  "impressions": 125,
  "clicks": 45,
  "likes": 12,
  "saves": 8,
  "skips": 3,
  "watch_starts": 10,
  "watch_completes": 6
}
```

### Interaction

Immutable interaction audit record created by `interaction-service`.

**Fields:**
- `id`: UUID (primary key)
- `event_id`: UUID, unique idempotency boundary for the ingested event
- `schema_name`: explicit schema identifier, currently `interaction_event.v1`
- `event_type`: enum (`impression`, `click`, `like`, `save`, `skip`, `watch_start`, `watch_complete`)
- `user_id`: UUID of the acting user
- `content_id`: UUID of the content item
- `session_id`: optional request/session identifier
- `topic`: optional normalized topic slug
- `watch_duration_seconds`: non-negative integer
- `metadata`: JSON metadata attached by the caller
- `event_payload`: canonical event payload stored for replay
- `kafka_topic`: currently `interactions.events.v1`
- `request_id`: request-scoped identifier for tracing
- `correlation_id`: distributed correlation identifier
- `event_timestamp`: time the event occurred
- `created_at`: time the service persisted the event
- `published_at`: time the event was successfully published to Kafka, nullable on broker failure

**Indexes:**
- event_id
- schema_name
- event_type
- user_id
- content_id
- session_id
- topic
- kafka_topic
- request_id
- correlation_id
- event_timestamp
- created_at
- published_at

## Data Types and Constraints

### Shared Constraints

- All IDs are UUID (v4) strings, 36 characters
- All timestamps are DateTime with UTC timezone
- JSON fields store untyped objects for flexibility
- Topic preferences are floats in range [0, 1]

### Validation Rules

**User:**
- username: 3-255 characters, unique per email realm
- email: valid email format, unique across system

**UserProfile:**
- bio: optional, max 500 characters
- topic_preferences: record of topic → score (0-1)

**ContentTag:**
- name: 1-255 characters, unique
- description: optional, max 500 characters

**ContentItem:**
- title: required, 5-500 characters
- description: optional, max 2000 characters
- topic: required, any string
- category: required, must be one of enum values
- status: required, "draft" or "published"

## Future Extensions

Phase 2 and beyond will add:

- `UserInteractions` - user engagement events with temporal tracking
- `UserTopicScores` - computed affinity scores for ranking
- `ContentFeatureSnapshots` - periodic feature materialization
- `FeedImpressions` - per-feed ranking decisions
- `ExperimentAssignments` - A/B test assignments
- `RankingDecisions` - scoring and explainability data

These will enable:
- Real-time preference tracking
- Historical analysis
- Experiment tracking
- Feed ranking and personalization
