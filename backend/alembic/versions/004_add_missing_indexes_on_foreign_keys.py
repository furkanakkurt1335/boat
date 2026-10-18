"""Add missing indexes on foreign keys.

Revision ID: 004
Revises: 003
Create Date: 2026-03-20
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(op.f("ix_sentences_treebank_id"), "sentences", ["treebank_id"])
    op.create_index(op.f("ix_annotations_annotator_id"), "annotations", ["annotator_id"])
    op.create_index(op.f("ix_annotations_sentence_id"), "annotations", ["sentence_id"])
    op.create_index(op.f("ix_comments_user_id"), "comments", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_comments_user_id"), table_name="comments")
    op.drop_index(op.f("ix_annotations_sentence_id"), table_name="annotations")
    op.drop_index(op.f("ix_annotations_annotator_id"), table_name="annotations")
    op.drop_index(op.f("ix_sentences_treebank_id"), table_name="sentences")
