"""add is_verified to enrolled_users

Revision ID: 3d33075ed47d
Revises: 0741f2a57a9d
Create Date: 2026-07-15 10:14:35.951426

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3d33075ed47d'
down_revision: Union[str, None] = '0741f2a57a9d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'enrolled_users',
        sa.Column(
            'is_verified',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column('enrolled_users', 'is_verified')