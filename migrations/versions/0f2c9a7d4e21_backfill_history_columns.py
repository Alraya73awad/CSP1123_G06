"""ensure all history columns exist

Revision ID: 0f2c9a7d4e21
Revises: 9b6f2a3c1d0e
Create Date: 2026-02-07 13:45:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0f2c9a7d4e21"
down_revision = "9b6f2a3c1d0e"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_logic INTEGER;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_logic INTEGER;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_weapon_atk INTEGER;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_weapon_atk INTEGER;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_weapon_type VARCHAR(20);")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_weapon_type VARCHAR(20);")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_weapon_name VARCHAR(50);")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_weapon_name VARCHAR(50);")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_algorithm VARCHAR(50);")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_algorithm VARCHAR(50);")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_upgrade_armor_plating BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_upgrade_overclock_unit BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_upgrade_regen_core BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_upgrade_critical_subroutine BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_upgrade_energy_recycler BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot1_upgrade_emp_shield BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_upgrade_armor_plating BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_upgrade_overclock_unit BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_upgrade_regen_core BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_upgrade_critical_subroutine BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_upgrade_energy_recycler BOOLEAN;")
        op.execute("ALTER TABLE history ADD COLUMN IF NOT EXISTS bot2_upgrade_emp_shield BOOLEAN;")
        return

    existing = set()
    result = bind.execute(sa.text("PRAGMA table_info(history);"))
    for row in result:
        existing.add(row[1])

    def add_col(name, column):
        if name not in existing:
            op.add_column("history", column)

    add_col("bot1_logic", sa.Column("bot1_logic", sa.Integer(), nullable=True))
    add_col("bot2_logic", sa.Column("bot2_logic", sa.Integer(), nullable=True))
    add_col("bot1_weapon_atk", sa.Column("bot1_weapon_atk", sa.Integer(), nullable=True))
    add_col("bot2_weapon_atk", sa.Column("bot2_weapon_atk", sa.Integer(), nullable=True))
    add_col("bot1_weapon_type", sa.Column("bot1_weapon_type", sa.String(length=20), nullable=True))
    add_col("bot2_weapon_type", sa.Column("bot2_weapon_type", sa.String(length=20), nullable=True))
    add_col("bot1_weapon_name", sa.Column("bot1_weapon_name", sa.String(length=50), nullable=True))
    add_col("bot2_weapon_name", sa.Column("bot2_weapon_name", sa.String(length=50), nullable=True))
    add_col("bot1_algorithm", sa.Column("bot1_algorithm", sa.String(length=50), nullable=True))
    add_col("bot2_algorithm", sa.Column("bot2_algorithm", sa.String(length=50), nullable=True))
    add_col("bot1_upgrade_armor_plating", sa.Column("bot1_upgrade_armor_plating", sa.Boolean(), nullable=True))
    add_col("bot1_upgrade_overclock_unit", sa.Column("bot1_upgrade_overclock_unit", sa.Boolean(), nullable=True))
    add_col("bot1_upgrade_regen_core", sa.Column("bot1_upgrade_regen_core", sa.Boolean(), nullable=True))
    add_col("bot1_upgrade_critical_subroutine", sa.Column("bot1_upgrade_critical_subroutine", sa.Boolean(), nullable=True))
    add_col("bot1_upgrade_energy_recycler", sa.Column("bot1_upgrade_energy_recycler", sa.Boolean(), nullable=True))
    add_col("bot1_upgrade_emp_shield", sa.Column("bot1_upgrade_emp_shield", sa.Boolean(), nullable=True))
    add_col("bot2_upgrade_armor_plating", sa.Column("bot2_upgrade_armor_plating", sa.Boolean(), nullable=True))
    add_col("bot2_upgrade_overclock_unit", sa.Column("bot2_upgrade_overclock_unit", sa.Boolean(), nullable=True))
    add_col("bot2_upgrade_regen_core", sa.Column("bot2_upgrade_regen_core", sa.Boolean(), nullable=True))
    add_col("bot2_upgrade_critical_subroutine", sa.Column("bot2_upgrade_critical_subroutine", sa.Boolean(), nullable=True))
    add_col("bot2_upgrade_energy_recycler", sa.Column("bot2_upgrade_energy_recycler", sa.Boolean(), nullable=True))
    add_col("bot2_upgrade_emp_shield", sa.Column("bot2_upgrade_emp_shield", sa.Boolean(), nullable=True))


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
        batch_op.drop_column("bot2_algorithm")
        batch_op.drop_column("bot1_algorithm")
        batch_op.drop_column("bot2_weapon_name")
        batch_op.drop_column("bot1_weapon_name")
        batch_op.drop_column("bot2_weapon_type")
        batch_op.drop_column("bot1_weapon_type")
        batch_op.drop_column("bot2_weapon_atk")
        batch_op.drop_column("bot1_weapon_atk")
        batch_op.drop_column("bot2_logic")
        batch_op.drop_column("bot1_logic")
