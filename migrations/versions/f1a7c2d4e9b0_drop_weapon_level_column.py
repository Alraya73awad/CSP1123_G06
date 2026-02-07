"""drop global weapon level column

Revision ID: f1a7c2d4e9b0
Revises: d4b2c9e1a7f8
Create Date: 2026-02-07 15:05:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1a7c2d4e9b0"
down_revision = "d4b2c9e1a7f8"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    def existing_cols(table_name):
        if dialect == "postgresql":
            result = bind.execute(
                sa.text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = :t
                    """
                ),
                {"t": table_name},
            )
            return {row[0] for row in result}
        result = bind.execute(sa.text(f"PRAGMA table_info({table_name});"))
        return {row[1] for row in result}

    if "level" in existing_cols("weapons"):
        with op.batch_alter_table("weapons", schema=None) as batch_op:
            batch_op.drop_column("level")


def downgrade():
    with op.batch_alter_table("weapons", schema=None) as batch_op:
        batch_op.add_column(sa.Column("level", sa.Integer(), nullable=True))
