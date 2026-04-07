"""Initial migration for content-service: create content_items and content_tags tables.

Revision ID: 001
Revises:
Create Date: 2026-04-07 19:05:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables: content_tags and content_items."""
    # Create content_tags table
    op.create_table(
        'content_tags',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_content_tags_name'), 'content_tags', ['name'])

    # Create content_items table
    op.create_table(
        'content_items',
        sa.Column('id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('topic', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'draft'")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('view_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('engagement_metadata', sa.JSON, nullable=False, server_default=sa.text("'{}'")),
        sa.CheckConstraint(
            "category IN ('ai', 'backend', 'system-design', 'devops', 'interview-prep')",
            name='ck_content_items_category',
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published')",
            name='ck_content_items_status',
        ),
    )
    op.create_index(op.f('ix_content_items_title'), 'content_items', ['title'])
    op.create_index(op.f('ix_content_items_topic'), 'content_items', ['topic'])
    op.create_index(op.f('ix_content_items_category'), 'content_items', ['category'])
    op.create_index(op.f('ix_content_items_status'), 'content_items', ['status'])
    op.create_index(op.f('ix_content_items_created_at'), 'content_items', ['created_at'])
    op.create_index(op.f('ix_content_items_published_at'), 'content_items', ['published_at'])

    # Create association table for many-to-many relationship
    op.create_table(
        'content_tags_association',
        sa.Column('content_id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('tag_id', sa.String(36), nullable=False, primary_key=True),
        sa.ForeignKeyConstraint(['content_id'], ['content_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['content_tags.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_content_tags_association_content_id', 'content_tags_association', ['content_id'])
    op.create_index('ix_content_tags_association_tag_id', 'content_tags_association', ['tag_id'])


def downgrade() -> None:
    """Drop tables in reverse order."""
    op.drop_index('ix_content_tags_association_tag_id', table_name='content_tags_association')
    op.drop_index('ix_content_tags_association_content_id', table_name='content_tags_association')
    op.drop_table('content_tags_association')

    op.drop_index(op.f('ix_content_items_published_at'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_created_at'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_status'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_category'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_topic'), table_name='content_items')
    op.drop_index(op.f('ix_content_items_title'), table_name='content_items')
    op.drop_table('content_items')

    op.drop_index(op.f('ix_content_tags_name'), table_name='content_tags')
    op.drop_table('content_tags')
