"""Initial migration for experimentation-service experiment assignments and exposures.

Revision ID: 001
Revises:
Create Date: 2026-04-08 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create experiment assignment and exposure tables."""

    op.create_table(
        "experiment_assignments",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("schema_name", sa.String(64), nullable=False),
        sa.Column("experiment_key", sa.String(120), nullable=False),
        sa.Column("variant_key", sa.String(120), nullable=False),
        sa.Column("strategy_name", sa.String(120), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("assignment_bucket", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "experiment_key",
            "user_id",
            name="uq_experiment_assignments_experiment_user",
        ),
        sa.CheckConstraint(
            "schema_name = 'experiment_assignment.v1'",
            name="ck_experiment_assignments_schema_name",
        ),
    )
    op.create_index(
        op.f("ix_experiment_assignments_experiment_key"),
        "experiment_assignments",
        ["experiment_key"],
    )
    op.create_index(
        op.f("ix_experiment_assignments_variant_key"),
        "experiment_assignments",
        ["variant_key"],
    )
    op.create_index(
        op.f("ix_experiment_assignments_strategy_name"),
        "experiment_assignments",
        ["strategy_name"],
    )
    op.create_index(
        op.f("ix_experiment_assignments_user_id"),
        "experiment_assignments",
        ["user_id"],
    )
    op.create_index(
        op.f("ix_experiment_assignments_assigned_at"),
        "experiment_assignments",
        ["assigned_at"],
    )

    op.create_table(
        "experiment_exposures",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("schema_name", sa.String(64), nullable=False),
        sa.Column("experiment_key", sa.String(120), nullable=False),
        sa.Column("variant_key", sa.String(120), nullable=False),
        sa.Column("strategy_name", sa.String(120), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("request_id", sa.String(64), nullable=False),
        sa.Column("correlation_id", sa.String(64), nullable=False),
        sa.Column("feed_limit", sa.Integer(), nullable=False),
        sa.Column("feed_offset", sa.Integer(), nullable=False),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "schema_name = 'experiment_exposure.v1'",
            name="ck_experiment_exposures_schema_name",
        ),
    )
    op.create_index(
        op.f("ix_experiment_exposures_experiment_key"),
        "experiment_exposures",
        ["experiment_key"],
    )
    op.create_index(
        op.f("ix_experiment_exposures_variant_key"),
        "experiment_exposures",
        ["variant_key"],
    )
    op.create_index(
        op.f("ix_experiment_exposures_strategy_name"),
        "experiment_exposures",
        ["strategy_name"],
    )
    op.create_index(
        op.f("ix_experiment_exposures_user_id"),
        "experiment_exposures",
        ["user_id"],
    )
    op.create_index(
        op.f("ix_experiment_exposures_session_id"),
        "experiment_exposures",
        ["session_id"],
    )
    op.create_index(
        op.f("ix_experiment_exposures_request_id"),
        "experiment_exposures",
        ["request_id"],
    )
    op.create_index(
        op.f("ix_experiment_exposures_correlation_id"),
        "experiment_exposures",
        ["correlation_id"],
    )
    op.create_index(
        op.f("ix_experiment_exposures_generated_at"),
        "experiment_exposures",
        ["generated_at"],
    )
    op.create_index(
        op.f("ix_experiment_exposures_created_at"),
        "experiment_exposures",
        ["created_at"],
    )

    op.create_table(
        "experiment_exposure_items",
        sa.Column("id", sa.String(36), nullable=False, primary_key=True),
        sa.Column("exposure_id", sa.String(36), nullable=False),
        sa.Column("content_id", sa.String(36), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("topic", sa.String(100), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["exposure_id"],
            ["experiment_exposures.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "exposure_id",
            "content_id",
            name="uq_experiment_exposure_items_exposure_content",
        ),
    )
    op.create_index(
        op.f("ix_experiment_exposure_items_exposure_id"),
        "experiment_exposure_items",
        ["exposure_id"],
    )
    op.create_index(
        op.f("ix_experiment_exposure_items_content_id"),
        "experiment_exposure_items",
        ["content_id"],
    )
    op.create_index(
        op.f("ix_experiment_exposure_items_topic"),
        "experiment_exposure_items",
        ["topic"],
    )
    op.create_index(
        op.f("ix_experiment_exposure_items_category"),
        "experiment_exposure_items",
        ["category"],
    )


def downgrade() -> None:
    """Drop experiment assignment and exposure tables."""

    op.drop_index(
        op.f("ix_experiment_exposure_items_category"),
        table_name="experiment_exposure_items",
    )
    op.drop_index(
        op.f("ix_experiment_exposure_items_topic"),
        table_name="experiment_exposure_items",
    )
    op.drop_index(
        op.f("ix_experiment_exposure_items_content_id"),
        table_name="experiment_exposure_items",
    )
    op.drop_index(
        op.f("ix_experiment_exposure_items_exposure_id"),
        table_name="experiment_exposure_items",
    )
    op.drop_table("experiment_exposure_items")

    op.drop_index(
        op.f("ix_experiment_exposures_created_at"),
        table_name="experiment_exposures",
    )
    op.drop_index(
        op.f("ix_experiment_exposures_generated_at"),
        table_name="experiment_exposures",
    )
    op.drop_index(
        op.f("ix_experiment_exposures_correlation_id"),
        table_name="experiment_exposures",
    )
    op.drop_index(
        op.f("ix_experiment_exposures_request_id"),
        table_name="experiment_exposures",
    )
    op.drop_index(
        op.f("ix_experiment_exposures_session_id"),
        table_name="experiment_exposures",
    )
    op.drop_index(
        op.f("ix_experiment_exposures_user_id"),
        table_name="experiment_exposures",
    )
    op.drop_index(
        op.f("ix_experiment_exposures_strategy_name"),
        table_name="experiment_exposures",
    )
    op.drop_index(
        op.f("ix_experiment_exposures_variant_key"),
        table_name="experiment_exposures",
    )
    op.drop_index(
        op.f("ix_experiment_exposures_experiment_key"),
        table_name="experiment_exposures",
    )
    op.drop_table("experiment_exposures")

    op.drop_index(
        op.f("ix_experiment_assignments_assigned_at"),
        table_name="experiment_assignments",
    )
    op.drop_index(
        op.f("ix_experiment_assignments_user_id"),
        table_name="experiment_assignments",
    )
    op.drop_index(
        op.f("ix_experiment_assignments_strategy_name"),
        table_name="experiment_assignments",
    )
    op.drop_index(
        op.f("ix_experiment_assignments_variant_key"),
        table_name="experiment_assignments",
    )
    op.drop_index(
        op.f("ix_experiment_assignments_experiment_key"),
        table_name="experiment_assignments",
    )
    op.drop_table("experiment_assignments")
