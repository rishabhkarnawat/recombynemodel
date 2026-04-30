"""Alembic migration: Phase 2 persistence (queries + watchlist).

Revision ID: 0001_phase2_persistence
Revises:
Create Date: 2026-04-30
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_phase2_persistence"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create queries and watchlist tables for Phase 2 persistence."""

    op.create_table(
        "queries",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("topic", sa.String(length=255), index=True),
        sa.Column("sources", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("window_hours", sa.Integer(), nullable=False, server_default="168"),
        sa.Column("raw_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("weighted_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("divergence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("divergence_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("post_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("queried_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("runtime_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("full_result", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_queries_queried_at", "queries", ["queried_at"])

    op.create_table(
        "watchlist",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("topic", sa.String(length=255), index=True),
        sa.Column("sources", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("window_hours", sa.Integer(), nullable=False, server_default="168"),
        sa.Column(
            "refresh_interval_minutes",
            sa.Integer(),
            nullable=False,
            server_default="60",
        ),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_weighted_score", sa.Float(), nullable=True),
        sa.Column("delta_since_last", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    """Drop Phase 2 persistence tables."""

    op.drop_table("watchlist")
    op.drop_index("ix_queries_queried_at", table_name="queries")
    op.drop_table("queries")
