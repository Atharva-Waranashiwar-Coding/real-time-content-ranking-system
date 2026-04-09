# Demo Scenarios

This document defines the deterministic demo contract used by the seed scripts and the frontend walkthrough.

## Setup Contract

Run this before a demo:

```bash
export DEMO_REFERENCE_TIME=2026-04-08T14:00:00+00:00
export RANKING_FIXED_NOW=2026-04-08T14:00:00+00:00
bash scripts/setup_demo.sh
```

Why both values matter:

- `DEMO_REFERENCE_TIME` anchors seeded content timestamps, feature snapshots, experiment exposures, and demo analytics rows.
- `RANKING_FIXED_NOW` freezes recency scoring so the score breakdown stays stable during the walkthrough.

If you do not need a fully frozen clock, you can skip both exports and still use `bash scripts/setup_demo.sh`.

## Canonical Users

| User | Variant | Assignment Bucket | Narrative |
| --- | --- | ---: | --- |
| `alice_dev` | `control` | `2371` | AI-first personalized feed with system design support |
| `bob_engineer` | `control` | `2377` | Backend-heavy feed with distributed systems content |
| `charlie_sysadmin` | `control` | `1011` | DevOps and observability leaning feed |
| `dana_ml` | `trending_boost` | `6576` | AI-heavy user in the trending boost strategy |
| `emma_fullstack` | `trending_boost` | `6581` | Interview-prep and backend blend in the trending boost strategy |

## Recommended Walkthrough

### Scenario 1: Explainable personalization

- Select `alice_dev` on `/feed`.
- Open the score drawer for the top ranked item.
- Explain how user topic affinity and recency combine with engagement and trending inputs.
- Expected hero items:
  - `Retrieval Augmented Generation (RAG)`
  - `Scalability Fundamentals`
  - `Prompt Engineering Best Practices`

### Scenario 2: Different user, different retrieval mix

- Switch to `bob_engineer`.
- Point out how backend and system-design items overtake AI-heavy content.
- Expected hero items:
  - `Message Queues and Event Streaming`
  - `REST API Design Patterns`
  - `Service Discovery`

### Scenario 3: Product + platform story

- Switch to `charlie_sysadmin`.
- Move from `/feed` to `/insights`.
- Use the topic chart and trending chart to connect user interests with platform/observability content.
- Expected hero items:
  - `Monitoring and Observability`
  - `Kubernetes Basics`
  - `Load Balancing Strategies`

### Scenario 4: Experimentation story

- Select `dana_ml` or `emma_fullstack`.
- Open `/experiments`.
- Show that these users land in `rules_v2_with_trending_boost`.
- Use the comparison chart to explain why the trending-boost strategy currently wins on completion rate in the seeded dataset.

## What The Bootstrap Seeds

`bash scripts/setup_demo.sh` creates a clean, deterministic baseline:

- 5 canonical demo users with fixed UUIDs
- 50+ canonical content items with fixed UUIDs, tags, and draft/published mix
- Redis content feature hashes and user topic affinity hashes
- PostgreSQL feature snapshots for both content and user-topic features
- deterministic experiment assignments for all demo users
- deterministic experiment exposures and interaction outcomes so the analytics dashboard is not empty

## Demo Safety Notes

- The reset script only targets demo records and feature keys derived from the canonical dataset.
- Feed caches for demo users are cleared during reset so a fresh run starts from the same baseline.
- The browser event stream widget is session-local; use the clear action in the UI if you want a clean live event panel mid-demo.
