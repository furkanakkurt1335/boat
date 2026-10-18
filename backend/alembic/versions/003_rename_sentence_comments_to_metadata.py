"""Rename sentences.comments to sentences.metadata.

Revision ID: 003
Revises: 002
Create Date: 2026-03-17
"""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("sentences", "comments", new_column_name="metadata")


def downgrade() -> None:
    op.alter_column("sentences", "metadata", new_column_name="comments")
