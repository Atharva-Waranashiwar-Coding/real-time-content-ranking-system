"""Initial migration for interaction-service: create interactions table.

Revision ID: 001
Revises:
Create Date: 2026-04-07 21:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the immutable interaction audit table."""

    op.create_table(
        "interactions",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("event_id", sa.String(36), nullable=False, unique=True),
        sa.Column("schema_name", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("content_id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("topic", sa.String(100), nullable=True),
        sa.Column("watch_duration_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.Column("kafka_topic", sa.String(100), nullable=False),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            (
                "event_type IN ("
                "'impression', 'click', 'like', 'save', 'skip', 'watch_start', 'watch_complete'"
                ")"
            ),
            name="ck_interactions_event_type",
        ),
        sa.CheckConstraint(
            "schema_name = 'interaction_event.v1'",
            name="ck_interactions_schema_name",
        ),
    )

    op.create_index(op.f("ix_interactions_event_id"), "interactions", ["event_id"])
    op.create_index(op.f("ix_interactions_schema_name"), "interactions", ["schema_name"])
    op.create_index(op.f("ix_interactions_event_type"), "interactions", ["event_type"])
    op.create_index(op.f("ix_interactions_user_id"), "interactions", ["user_id"])
    op.create_index(op.f("ix_interactions_content_id"), "interactions", ["content_id"])
    op.create_index(op.f("ix_interactions_session_id"), "interactions", ["session_id"])
    op.create_index(op.f("ix_interactions_topic"), "interactions", ["topic"])
    op.create_index(op.f("ix_interactions_kafka_topic"), "interactions", ["kafka_topic"])
    op.create_index(op.f("ix_interactions_request_id"), "interactions", ["request_id"])
    op.create_index(op.f("ix_interactions_correlation_id"), "interactions", ["correlation_id"])
    op.create_index(op.f("ix_interactions_event_timestamp"), "interactions", ["event_timestamp"])
    op.create_index(op.f("ix_interactions_created_at"), "interactions", ["created_at"])
    op.create_index(op.f("ix_interactions_published_at"), "interactions", ["published_at"])


def downgrade() -> None:
    """Drop the interactions table and its indexes."""

    op.drop_index(op.f("ix_interactions_published_at"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_created_at"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_event_timestamp"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_correlation_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_request_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_kafka_topic"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_topic"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_session_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_content_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_user_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_event_type"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_schema_name"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_event_id"), table_name="interactions")
    op.drop_table("interactions")
