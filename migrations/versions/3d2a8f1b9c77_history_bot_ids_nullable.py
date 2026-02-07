"""make history bot ids nullable

Revision ID: 3d2a8f1b9c77
Revises: 2c7b1d9e4a10
Create Date: 2026-02-07 14:10:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3d2a8f1b9c77"
down_revision = "2c7b1d9e4a10"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("history", schema=None) as batch_op:
        batch_op.alter_column("bot1_id", existing_type=sa.Integer(), nullable=True)
        batch_op.alter_column("bot2_id", existing_type=sa.Integer(), nullable=True)


def downgrade():
    with op.batch_alter_table("history", schema=None) as batch_op:
        batch_op.alter_column("bot2_id", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("bot1_id", existing_type=sa.Integer(), nullable=False)
