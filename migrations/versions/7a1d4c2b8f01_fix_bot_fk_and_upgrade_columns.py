"""fix bot fk and add upgrade columns

Revision ID: 7a1d4c2b8f01
Revises: b5e28b16b462
Create Date: 2026-02-07 12:05:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7a1d4c2b8f01"
down_revision = "b5e28b16b462"
branch_labels = None
depends_on = None


def upgrade():
    # Ensure table name matches model: bots
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.bot') IS NOT NULL AND to_regclass('public.bots') IS NULL THEN
                ALTER TABLE public.bot RENAME TO bots;
            END IF;
        END$$;
        """
    )

    # Fix FK to reference bots table
    op.execute("ALTER TABLE weapon_ownership DROP CONSTRAINT IF EXISTS weapon_ownership_bot_id_fkey;")
    op.execute(
        """
        ALTER TABLE weapon_ownership
        ADD CONSTRAINT weapon_ownership_bot_id_fkey
        FOREIGN KEY (bot_id) REFERENCES bots (id) ON DELETE SET NULL;
        """
    )

    bind = op.get_bind()
    dialect = bind.dialect.name

    def existing_cols(table_name):
        cols = set()
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
            cols = {row[0] for row in result}
        else:
            result = bind.execute(sa.text(f"PRAGMA table_info({table_name});"))
            cols = {row[1] for row in result}
        return cols

    bots_cols = existing_cols("bots")
    history_cols = existing_cols("history")

    # Bot upgrade flags
    with op.batch_alter_table("bots", schema=None) as batch_op:
        if "upgrade_armor_plating" not in bots_cols:
            batch_op.add_column(sa.Column("upgrade_armor_plating", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "upgrade_overclock_unit" not in bots_cols:
            batch_op.add_column(sa.Column("upgrade_overclock_unit", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "upgrade_regen_core" not in bots_cols:
            batch_op.add_column(sa.Column("upgrade_regen_core", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "upgrade_critical_subroutine" not in bots_cols:
            batch_op.add_column(sa.Column("upgrade_critical_subroutine", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "upgrade_energy_recycler" not in bots_cols:
            batch_op.add_column(sa.Column("upgrade_energy_recycler", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "upgrade_emp_shield" not in bots_cols:
            batch_op.add_column(sa.Column("upgrade_emp_shield", sa.Boolean(), server_default=sa.text("false"), nullable=False))

    # History fields
    with op.batch_alter_table("history", schema=None) as batch_op:
        if "bot1_weapon_name" not in history_cols:
            batch_op.add_column(sa.Column("bot1_weapon_name", sa.String(length=50), nullable=True))
        if "bot2_weapon_name" not in history_cols:
            batch_op.add_column(sa.Column("bot2_weapon_name", sa.String(length=50), nullable=True))
        if "bot1_upgrade_armor_plating" not in history_cols:
            batch_op.add_column(sa.Column("bot1_upgrade_armor_plating", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot1_upgrade_overclock_unit" not in history_cols:
            batch_op.add_column(sa.Column("bot1_upgrade_overclock_unit", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot1_upgrade_regen_core" not in history_cols:
            batch_op.add_column(sa.Column("bot1_upgrade_regen_core", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot1_upgrade_critical_subroutine" not in history_cols:
            batch_op.add_column(sa.Column("bot1_upgrade_critical_subroutine", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot1_upgrade_energy_recycler" not in history_cols:
            batch_op.add_column(sa.Column("bot1_upgrade_energy_recycler", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot1_upgrade_emp_shield" not in history_cols:
            batch_op.add_column(sa.Column("bot1_upgrade_emp_shield", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot2_upgrade_armor_plating" not in history_cols:
            batch_op.add_column(sa.Column("bot2_upgrade_armor_plating", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot2_upgrade_overclock_unit" not in history_cols:
            batch_op.add_column(sa.Column("bot2_upgrade_overclock_unit", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot2_upgrade_regen_core" not in history_cols:
            batch_op.add_column(sa.Column("bot2_upgrade_regen_core", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot2_upgrade_critical_subroutine" not in history_cols:
            batch_op.add_column(sa.Column("bot2_upgrade_critical_subroutine", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot2_upgrade_energy_recycler" not in history_cols:
            batch_op.add_column(sa.Column("bot2_upgrade_energy_recycler", sa.Boolean(), server_default=sa.text("false"), nullable=False))
        if "bot2_upgrade_emp_shield" not in history_cols:
            batch_op.add_column(sa.Column("bot2_upgrade_emp_shield", sa.Boolean(), server_default=sa.text("false"), nullable=False))


def downgrade():
    with op.batch_alter_table("history", schema=None) as batch_op:
        batch_op.drop_column("bot2_upgrade_emp_shield")
        batch_op.drop_column("bot2_upgrade_energy_recycler")
        batch_op.drop_column("bot2_upgrade_critical_subroutine")
        batch_op.drop_column("bot2_upgrade_regen_core")
        batch_op.drop_column("bot2_upgrade_overclock_unit")
        batch_op.drop_column("bot2_upgrade_armor_plating")
        batch_op.drop_column("bot1_upgrade_emp_shield")
        batch_op.drop_column("bot1_upgrade_energy_recycler")
        batch_op.drop_column("bot1_upgrade_critical_subroutine")
        batch_op.drop_column("bot1_upgrade_regen_core")
        batch_op.drop_column("bot1_upgrade_overclock_unit")
        batch_op.drop_column("bot1_upgrade_armor_plating")
        batch_op.drop_column("bot2_weapon_name")
        batch_op.drop_column("bot1_weapon_name")

    with op.batch_alter_table("bots", schema=None) as batch_op:
        batch_op.drop_column("upgrade_emp_shield")
        batch_op.drop_column("upgrade_energy_recycler")
        batch_op.drop_column("upgrade_critical_subroutine")
        batch_op.drop_column("upgrade_regen_core")
        batch_op.drop_column("upgrade_overclock_unit")
        batch_op.drop_column("upgrade_armor_plating")

    op.execute("ALTER TABLE weapon_ownership DROP CONSTRAINT IF EXISTS weapon_ownership_bot_id_fkey;")
    op.execute(
        """
        DO $$
        BEGIN
            IF to_regclass('public.bot') IS NOT NULL THEN
                ALTER TABLE weapon_ownership
                ADD CONSTRAINT weapon_ownership_bot_id_fkey
                FOREIGN KEY (bot_id) REFERENCES bot (id);
            ELSIF to_regclass('public.bots') IS NOT NULL THEN
                ALTER TABLE weapon_ownership
                ADD CONSTRAINT weapon_ownership_bot_id_fkey
                FOREIGN KEY (bot_id) REFERENCES bots (id);
            END IF;
        END$$;
        """
    )
