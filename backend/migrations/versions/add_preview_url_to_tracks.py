"""add preview_url to tracks

Revision ID: add_preview_url
Revises: 6031458585cd
Create Date: 2026-02-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "add_preview_url"
down_revision: Union[str, Sequence[str], None] = "6031458585cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tracks", sa.Column("preview_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("tracks", "preview_url")
