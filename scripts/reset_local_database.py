"""Reset the local PostgreSQL public schema for a clean migration run."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


def _database_dsn() -> str:
    """Build a synchronous PostgreSQL DSN from environment variables."""

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    user = os.getenv("DB_USER", "rankinguser")
    password = os.getenv("DB_PASSWORD", "rankingpass")
    db_name = os.getenv("DB_NAME", "ranking_db")
    return f"host={host} port={port} dbname={db_name} user={user} password={password}"


def reset_local_database() -> None:
    """Drop and recreate the public schema used by local development."""

    load_dotenv()

    connection = connect(_database_dsn())
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    try:
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA IF EXISTS public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")
            cursor.execute('GRANT ALL ON SCHEMA public TO CURRENT_USER;')
            cursor.execute("GRANT ALL ON SCHEMA public TO public;")
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            cursor.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm";')
    finally:
        connection.close()

    print("Reset local PostgreSQL schema: public")


if __name__ == "__main__":
    reset_local_database()
