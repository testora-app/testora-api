"""add description to topic

Revision ID: 2026060418
Revises: 2026060318
Create Date: 2026-06-04 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026060418"
down_revision = "2026060318"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("topic", schema=None) as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("topic", schema=None) as batch_op:
        batch_op.drop_column("description")
