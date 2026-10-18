"""Initial migration — create all tables.

Revision ID: 001
Revises:
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(150), nullable=False, unique=True, index=True),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("first_name", sa.String(150), nullable=False),
        sa.Column("last_name", sa.String(150), nullable=False),
        sa.Column("hashed_password", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("preferences", sa.JSON, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "treebanks",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(30), nullable=False, unique=True, index=True),
        sa.Column("language", sa.String(30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "sentences",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column(
            "treebank_id",
            sa.Integer,
            sa.ForeignKey("treebanks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sent_id", sa.String(30), nullable=False, index=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("sent_id", "text", "treebank_id"),
    )

    op.create_table(
        "annotations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "annotator_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sentence_id",
            sa.Integer,
            sa.ForeignKey("sentences.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("notes", sa.Text, nullable=False, server_default=sa.text("''")),
        sa.Column("status", sa.SmallInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("is_template", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("is_gold", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "wordlines",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "annotation_id",
            sa.Integer,
            sa.ForeignKey("annotations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("id_f", sa.String(10), nullable=False),
        sa.Column("form", sa.String(200), nullable=False),
        sa.Column("lemma", sa.String(200), nullable=False),
        sa.Column("upos", sa.String(20), nullable=False),
        sa.Column("xpos", sa.String(100), nullable=False),
        sa.Column("feats", sa.String(1000), nullable=False),
        sa.Column("head", sa.String(10), nullable=False),
        sa.Column("deprel", sa.String(100), nullable=False),
        sa.Column("deps", sa.String(200), nullable=False),
        sa.Column("misc", sa.String(500), nullable=False),
        sa.Column("feats_parsed", sa.JSON, nullable=True),
        sa.Column("misc_parsed", sa.JSON, nullable=True),
    )

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "sentence_id",
            sa.Integer,
            sa.ForeignKey("sentences.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "validation_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "treebank_id",
            sa.Integer,
            sa.ForeignKey("treebanks.id", ondelete="CASCADE"),
            nullable=True,
            unique=True,
        ),
        sa.Column("allowed_upos", sa.JSON, nullable=True),
        sa.Column("allowed_deprels", sa.JSON, nullable=True),
        sa.Column("allowed_features", sa.JSON, nullable=True),
        sa.Column("custom_rules", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "guidelines",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "treebank_id",
            sa.Integer,
            sa.ForeignKey("treebanks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("key", sa.String(100), nullable=False, index=True),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("guidelines")
    op.drop_table("validation_profiles")
    op.drop_table("comments")
    op.drop_table("wordlines")
    op.drop_table("annotations")
    op.drop_table("sentences")
    op.drop_table("treebanks")
    op.drop_table("users")
