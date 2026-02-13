"""add_trial_tier_and_cycle_switching

Revision ID: 2026021318
Revises: c0e6e8206343
Create Date: 2026-02-13 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2026021318'
down_revision = 'c0e6e8206343'
branch_labels = None
depends_on = None


def upgrade():
    # Add scheduled_billing_cycle and scheduled_billing_cycle_date columns
    with op.batch_alter_table("school", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("scheduled_billing_cycle", sa.String(length=20), nullable=True)
        )
        batch_op.add_column(
            sa.Column("scheduled_billing_cycle_date", sa.Date(), nullable=True)
        )

    # Backfill: Convert trial schools (those with unlimited seats) to new trial tier
    conn = op.get_bind()

    # Convert premium schools with 100000+ seats (unlimited trial) to trial tier
    conn.execute(
        sa.text(
            """
            UPDATE school
            SET subscription_tier = 'trial',
                total_seats = 100,
                billing_cycle = NULL,
                price_per_seat = 0
            WHERE subscription_tier = 'premium'
              AND total_seats >= 100000
            """
        )
    )

    # Paid premium schools remain unchanged


def downgrade():
    with op.batch_alter_table("school", schema=None) as batch_op:
        batch_op.drop_column("scheduled_billing_cycle_date")
        batch_op.drop_column("scheduled_billing_cycle")

    # Revert trial schools back to premium with unlimited seats
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            UPDATE school
            SET subscription_tier = 'premium',
                total_seats = 100000
            WHERE subscription_tier = 'trial'
            """
        )
    )
