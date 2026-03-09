"""school_subscription_tiers_and_seats

Revision ID: c0e6e8206343
Revises: 6a32cfea309d
Create Date: 2026-02-11 17:21:10.381164

"""
from alembic import op
import sqlalchemy as sa


# NOTE:
# We store subscription state on the `school` table as agreed.
#
# Backfill rules (confirmed):
# - Free tier defaults to 10 seats.
# - Existing Premium schools: total_seats = approved_students + 5.
# - Existing Premium schools: billing_cycle = monthly, price_per_seat = 75.
#
# seatsUsed is not stored; we compute it dynamically as the count of approved,
# not archived, not deleted students.


# revision identifiers, used by Alembic.
revision = 'c0e6e8206343'
down_revision = '6a32cfea309d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("school", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "subscription_tier",
                sa.String(length=32),
                nullable=False,
                server_default="free",
            )
        )
        batch_op.add_column(
            sa.Column(
                "billing_cycle",
                sa.String(length=16),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "total_seats",
                sa.Integer(),
                nullable=False,
                server_default="10",
            )
        )
        batch_op.add_column(
            sa.Column(
                "price_per_seat",
                sa.Float(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(sa.Column("scheduled_seat_reduction", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("scheduled_reduction_date", sa.Date(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "scheduled_downgrade",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )
        batch_op.add_column(sa.Column("scheduled_downgrade_date", sa.Date(), nullable=True))

    # Backfill from legacy subscription_package (values like 'Free'/'Premium')
    # into the new fields.
    conn = op.get_bind()

    # Default everything to free tier
    conn.execute(
        sa.text(
            """
            UPDATE school
            SET subscription_tier = 'free',
                billing_cycle = NULL,
                total_seats = 10,
                price_per_seat = 0
            """
        )
    )

    # Premium schools: tier=premium, monthly, 75 per seat, seats = approved_students + 5
    conn.execute(
        sa.text(
            """
            UPDATE school s
            SET subscription_tier = 'premium',
                billing_cycle = 'monthly',
                price_per_seat = 75,
                total_seats = COALESCE((
                    SELECT COUNT(1)
                    FROM student st
                    WHERE st.school_id = s.id
                      AND st.is_deleted = false
                      AND st.is_archived = false
                      AND st.is_approved = true
                ), 0) + 5
            WHERE LOWER(COALESCE(s.subscription_package, '')) LIKE '%premium%'
            """
        )
    )


def downgrade():
    with op.batch_alter_table("school", schema=None) as batch_op:
        batch_op.drop_column("scheduled_downgrade_date")
        batch_op.drop_column("scheduled_downgrade")
        batch_op.drop_column("scheduled_reduction_date")
        batch_op.drop_column("scheduled_seat_reduction")
        batch_op.drop_column("price_per_seat")
        batch_op.drop_column("total_seats")
        batch_op.drop_column("billing_cycle")
        batch_op.drop_column("subscription_tier")
