"""Initial migration for feature-processor: create feature snapshot tables.

Revision ID: 001
Revises:
Create Date: 2026-04-08 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create feature snapshot tables for content and user-topic vectors."""

    op.create_table(
        "content_feature_snapshots",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("schema_name", sa.String(64), nullable=False),
        sa.Column("content_id", sa.String(36), nullable=False),
        sa.Column("topic", sa.String(100), nullable=True),
        sa.Column("window_hours", sa.Integer(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skip_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("watch_starts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("watch_completes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ctr", sa.Float(), nullable=False, server_default="0"),
        sa.Column("like_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("save_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("skip_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("completion_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("trending_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "schema_name = 'content_features.v1'",
            name="ck_content_feature_snapshots_schema_name",
        ),
        sa.CheckConstraint(
            "window_hours > 0",
            name="ck_content_feature_snapshots_window_hours_positive",
        ),
    )
    op.create_index(
        op.f("ix_content_feature_snapshots_schema_name"),
        "content_feature_snapshots",
        ["schema_name"],
    )
    op.create_index(
        op.f("ix_content_feature_snapshots_content_id"),
        "content_feature_snapshots",
        ["content_id"],
    )
    op.create_index(
        op.f("ix_content_feature_snapshots_topic"),
        "content_feature_snapshots",
        ["topic"],
    )
    op.create_index(
        op.f("ix_content_feature_snapshots_snapshot_at"),
        "content_feature_snapshots",
        ["snapshot_at"],
    )
    op.create_index(
        op.f("ix_content_feature_snapshots_created_at"),
        "content_feature_snapshots",
        ["created_at"],
    )

    op.create_table(
        "user_topic_feature_snapshots",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("schema_name", sa.String(64), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("window_hours", sa.Integer(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("saves", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skip_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("watch_starts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("watch_completes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("affinity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("snapshot_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "schema_name = 'user_topic_affinity.v1'",
            name="ck_user_topic_feature_snapshots_schema_name",
        ),
        sa.CheckConstraint(
            "window_hours > 0",
            name="ck_user_topic_feature_snapshots_window_hours_positive",
        ),
    )
    op.create_index(
        op.f("ix_user_topic_feature_snapshots_schema_name"),
        "user_topic_feature_snapshots",
        ["schema_name"],
    )
    op.create_index(
        op.f("ix_user_topic_feature_snapshots_user_id"),
        "user_topic_feature_snapshots",
        ["user_id"],
    )
    op.create_index(
        op.f("ix_user_topic_feature_snapshots_topic"),
        "user_topic_feature_snapshots",
        ["topic"],
    )
    op.create_index(
        op.f("ix_user_topic_feature_snapshots_snapshot_at"),
        "user_topic_feature_snapshots",
        ["snapshot_at"],
    )
    op.create_index(
        op.f("ix_user_topic_feature_snapshots_created_at"),
        "user_topic_feature_snapshots",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop feature snapshot tables in reverse order."""

    op.drop_index(
        op.f("ix_user_topic_feature_snapshots_created_at"),
        table_name="user_topic_feature_snapshots",
    )
    op.drop_index(
        op.f("ix_user_topic_feature_snapshots_snapshot_at"),
        table_name="user_topic_feature_snapshots",
    )
    op.drop_index(
        op.f("ix_user_topic_feature_snapshots_topic"),
        table_name="user_topic_feature_snapshots",
    )
    op.drop_index(
        op.f("ix_user_topic_feature_snapshots_user_id"),
        table_name="user_topic_feature_snapshots",
    )
    op.drop_index(
        op.f("ix_user_topic_feature_snapshots_schema_name"),
        table_name="user_topic_feature_snapshots",
    )
    op.drop_table("user_topic_feature_snapshots")

    op.drop_index(
        op.f("ix_content_feature_snapshots_created_at"),
        table_name="content_feature_snapshots",
    )
    op.drop_index(
        op.f("ix_content_feature_snapshots_snapshot_at"),
        table_name="content_feature_snapshots",
    )
    op.drop_index(
        op.f("ix_content_feature_snapshots_topic"),
        table_name="content_feature_snapshots",
    )
    op.drop_index(
        op.f("ix_content_feature_snapshots_content_id"),
        table_name="content_feature_snapshots",
    )
    op.drop_index(
        op.f("ix_content_feature_snapshots_schema_name"),
        table_name="content_feature_snapshots",
    )
    op.drop_table("content_feature_snapshots")
