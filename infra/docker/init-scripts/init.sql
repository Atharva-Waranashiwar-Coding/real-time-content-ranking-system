-- Minimal PostgreSQL bootstrap for local development.
--
-- Service schemas are owned by Alembic migrations under each service.
-- This script only installs extensions that are useful across services.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
