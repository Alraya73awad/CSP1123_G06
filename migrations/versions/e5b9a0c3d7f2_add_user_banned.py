"""add user banned flag

Revision ID: e5b9a0c3d7f2
Revises: f1a7c2d4e9b0
Create Date: 2026-02-07 15:40:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e5b9a0c3d7f2"
down_revision = "f1a7c2d4e9b0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("banned", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("banned", server_default=None)


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("banned")
