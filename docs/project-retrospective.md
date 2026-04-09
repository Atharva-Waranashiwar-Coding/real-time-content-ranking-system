# Tradeoffs, Future Improvements, And Lessons Learned

## Architectural Tradeoffs

### Rules-based ranking before ML

Chosen because:

- deterministic outputs are easier to verify
- the frontend can explain every score contribution
- experiment analytics become easier to trust
- it keeps the first version interview-friendly

Tradeoff:

- the ranking quality ceiling is lower than a model-based system
- content understanding is limited to explicitly engineered features

### Redis materialization instead of direct analytical queries

Chosen because:

- feed generation needs low-latency feature reads
- feature freshness matters more than ad hoc query flexibility on the serving path

Tradeoff:

- another data store increases operational complexity
- feature consistency depends on the stream pipeline staying healthy

### Shared schemas in a monorepo

Chosen because:

- event contracts stay explicit and versioned
- backend services and frontend DTOs can evolve with fewer mismatches

Tradeoff:

- shared packages create tighter repository coupling
- local source execution needs bootstrap helpers because the package directories are intentionally repo-local

### Direct frontend-to-service API calls for the demo

Chosen because:

- it makes service contracts visible during a walkthrough
- each service can be inspected independently in a portfolio setting

Tradeoff:

- a production frontend would usually consolidate this behind a gateway or BFF
- client-side service awareness increases configuration surface area

## Future Improvements

### Ranking and ML

- replace the rules engine with a learned ranking model behind the same DTO boundary
- add richer content semantics such as embeddings and semantic similarity features
- include per-session fatigue, novelty, and creator-level diversity features

### Platform and Data

- move from a single Python consumer to a more elastic streaming runtime
- separate OLTP and analytics storage explicitly
- add offline backfills and replay tooling for feature regeneration

### Product

- add authentication and user sessions beyond the demo context
- add creator metadata, richer content bodies, and moderation signals
- expose historical interaction and ranking-decision views in the UI

### Operations

- add distributed tracing instead of correlation-ID-only tracing
- add circuit breakers and graceful degradation on upstream dependency failures
- harden topic management and broker topology beyond single-node local defaults

## Lessons Learned

- Explainability is easier to preserve if it is built into the DTOs from the beginning.
- Deterministic demo data is worth real engineering time; it improves both demos and tests.
- Experiment analytics are only credible when exposures and outcomes are modeled explicitly.
- Shared schemas remove an entire class of integration drift, but local developer ergonomics need to be designed alongside them.
- Observability should be part of the product story, especially in a systems-oriented portfolio project.

## What I Would Change First In A Production Follow-Up

1. Introduce authentication and a proper gateway or BFF for the frontend.
2. Add a ranking feature service boundary and online/offline feature parity checks.
3. Add a warehouse-oriented analytics path instead of relying only on service-owned OLTP tables.
4. Replace the demo bootstrap with repeatable environment automation and fixture loading in CI.
