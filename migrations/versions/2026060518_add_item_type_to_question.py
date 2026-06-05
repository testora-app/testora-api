"""add item_type to question

Revision ID: 2026060518
Revises: 2026060418
Create Date: 2026-06-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026060518"
down_revision = "2026060418"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("question", schema=None) as batch_op:
        batch_op.add_column(sa.Column("item_type", sa.String(length=40), nullable=True))


def downgrade():
    with op.batch_alter_table("question", schema=None) as batch_op:
        batch_op.drop_column("item_type")
