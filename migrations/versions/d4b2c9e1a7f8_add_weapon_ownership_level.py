"""add per-user weapon level to weapon_ownership

Revision ID: d4b2c9e1a7f8
Revises: 3d2a8f1b9c77
Create Date: 2026-02-07 14:45:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d4b2c9e1a7f8"
down_revision = "3d2a8f1b9c77"
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

    cols = existing_cols("weapon_ownership")
    if "level" not in cols:
        with op.batch_alter_table("weapon_ownership", schema=None) as batch_op:
            batch_op.add_column(sa.Column("level", sa.Integer(), nullable=False, server_default="1"))

    # Backfill from global weapon levels for existing ownerships (if column exists)
    cols_weapons = existing_cols("weapons")
    if "level" in cols_weapons:
        op.execute(
            """
            UPDATE weapon_ownership
            SET level = (
                SELECT weapons.level
                FROM weapons
                WHERE weapons.id = weapon_ownership.weapon_id
            )
            """
        )

    if "level" in cols_weapons:
        op.execute("UPDATE weapons SET level = 1")

    if "level" in existing_cols("weapon_ownership"):
        with op.batch_alter_table("weapon_ownership", schema=None) as batch_op:
            batch_op.alter_column("level", server_default=None)


def downgrade():
    with op.batch_alter_table("weapon_ownership", schema=None) as batch_op:
        batch_op.drop_column("level")
