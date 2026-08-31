"""catalog cache and sync states

Revision ID: 002_catalog_cache
Revises: 001_initial
"""

import sqlalchemy as sa
from alembic import op

revision = "002_catalog_cache"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("catalog_parts"):
        op.create_table(
            "catalog_parts",
            sa.Column("id", sa.String(100), primary_key=True),
            sa.Column("category", sa.String(30), nullable=False),
            sa.Column("source", sa.String(80), nullable=False),
            sa.Column("part_json", sa.Text(), nullable=False),
            sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_catalog_parts_category", "catalog_parts", ["category"])
        op.create_index("ix_catalog_parts_source", "catalog_parts", ["source"])
        op.create_index("ix_catalog_parts_expires_at", "catalog_parts", ["expires_at"])
    if not sa.inspect(bind).has_table("catalog_sync_states"):
        op.create_table(
            "catalog_sync_states",
            sa.Column("category", sa.String(30), primary_key=True),
            sa.Column("status", sa.String(30), nullable=False),
            sa.Column("provider", sa.String(80), nullable=False),
            sa.Column("item_count", sa.Integer(), nullable=False),
            sa.Column("message", sa.String(300), nullable=False),
            sa.Column("captured_at", sa.DateTime(timezone=True)),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
        op.create_index("ix_catalog_sync_states_status", "catalog_sync_states", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("catalog_sync_states"):
        op.drop_index("ix_catalog_sync_states_status", table_name="catalog_sync_states")
        op.drop_table("catalog_sync_states")
    if sa.inspect(bind).has_table("catalog_parts"):
        op.drop_index("ix_catalog_parts_expires_at", table_name="catalog_parts")
        op.drop_index("ix_catalog_parts_source", table_name="catalog_parts")
        op.drop_index("ix_catalog_parts_category", table_name="catalog_parts")
        op.drop_table("catalog_parts")
