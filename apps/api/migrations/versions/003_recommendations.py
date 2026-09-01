"""structured recommendations

Revision ID: 003_recommendations
Revises: 002_catalog_cache
"""

import sqlalchemy as sa
from alembic import op

revision = "003_recommendations"
down_revision = "002_catalog_cache"
branch_labels = None
depends_on = None


def _index_names(bind) -> set[str]:
    return {str(index["name"]) for index in sa.inspect(bind).get_indexes("recommendations")}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("recommendations"):
        op.create_table(
            "recommendations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("plan_id", sa.String(36), nullable=False),
            sa.Column("plan_fingerprint", sa.String(64), nullable=False),
            sa.Column("recommendation_json", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )
    indexes = _index_names(bind)
    if "ix_recommendations_plan_id" not in indexes:
        op.create_index("ix_recommendations_plan_id", "recommendations", ["plan_id"])
    if "ix_recommendations_plan_fingerprint" not in indexes:
        op.create_index(
            "ix_recommendations_plan_fingerprint",
            "recommendations",
            ["plan_fingerprint"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("recommendations"):
        return
    indexes = _index_names(bind)
    if "ix_recommendations_plan_fingerprint" in indexes:
        op.drop_index("ix_recommendations_plan_fingerprint", table_name="recommendations")
    if "ix_recommendations_plan_id" in indexes:
        op.drop_index("ix_recommendations_plan_id", table_name="recommendations")
    op.drop_table("recommendations")
