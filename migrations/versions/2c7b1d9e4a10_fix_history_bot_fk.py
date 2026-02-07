"""fix history bot fk to reference bots

Revision ID: 2c7b1d9e4a10
Revises: 0f2c9a7d4e21
Create Date: 2026-02-07 13:55:00.000000
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "2c7b1d9e4a10"
down_revision = "0f2c9a7d4e21"
branch_labels = None
depends_on = None


def upgrade():
    # Drop any existing FK that points to bot
    op.execute("ALTER TABLE history DROP CONSTRAINT IF EXISTS history_bot1_id_fkey;")
    op.execute("ALTER TABLE history DROP CONSTRAINT IF EXISTS history_bot2_id_fkey;")
    # Clean up invalid bot references before adding FK
    op.execute(
        """
        UPDATE history
        SET bot1_id = NULL
        WHERE bot1_id IS NOT NULL
          AND bot1_id NOT IN (SELECT id FROM bots);
        """
    )
    op.execute(
        """
        UPDATE history
        SET bot2_id = NULL
        WHERE bot2_id IS NOT NULL
          AND bot2_id NOT IN (SELECT id FROM bots);
        """
    )
    # Recreate FK to bots table
    op.execute(
        """
        ALTER TABLE history
        ADD CONSTRAINT history_bot1_id_fkey
        FOREIGN KEY (bot1_id) REFERENCES bots (id) ON DELETE SET NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE history
        ADD CONSTRAINT history_bot2_id_fkey
        FOREIGN KEY (bot2_id) REFERENCES bots (id) ON DELETE SET NULL;
        """
    )


def downgrade():
    op.execute("ALTER TABLE history DROP CONSTRAINT IF EXISTS history_bot1_id_fkey;")
    op.execute("ALTER TABLE history DROP CONSTRAINT IF EXISTS history_bot2_id_fkey;")
