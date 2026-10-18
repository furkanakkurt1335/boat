"""Add allowed_misc and feature_order to validation_profiles.

Revision ID: 002
Revises: 001
Create Date: 2026-03-17
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("validation_profiles", sa.Column("allowed_misc", sa.JSON, nullable=True))
    op.add_column("validation_profiles", sa.Column("feature_order", sa.JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("validation_profiles", "feature_order")
    op.drop_column("validation_profiles", "allowed_misc")
