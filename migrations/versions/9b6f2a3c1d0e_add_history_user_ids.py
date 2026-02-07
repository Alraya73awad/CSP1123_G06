"""add history user ids if missing

Revision ID: 9b6f2a3c1d0e
Revises: 7a1d4c2b8f01
Create Date: 2026-02-07 13:10:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b6f2a3c1d0e"
down_revision = "7a1d4c2b8f01"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS user1_id INTEGER;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS user2_id INTEGER;")
        return

    existing = set()
    result = bind.execute(sa.text("PRAGMA table_info(history);"))
    for row in result:
        existing.add(row[1])

    with op.batch_alter_table("history", schema=None) as batch_op:
        if "user1_id" not in existing:
            batch_op.add_column(sa.Column("user1_id", sa.Integer(), nullable=True))
        if "user2_id" not in existing:
            batch_op.add_column(sa.Column("user2_id", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("history", schema=None) as batch_op:
        batch_op.drop_column("user2_id")
        batch_op.drop_column("user1_id")
