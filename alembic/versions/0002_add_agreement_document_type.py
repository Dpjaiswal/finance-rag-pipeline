"""add agreement document type

Revision ID: 0002_add_agreement_document_type
Revises: 0001_initial
Create Date: 2026-05-23
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_add_agreement_document_type"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'agreement'")


def downgrade() -> None:
    # PostgreSQL enum values cannot be removed safely without recreating the enum.
    pass
