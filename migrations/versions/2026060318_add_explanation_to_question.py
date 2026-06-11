"""add explanation to question

Revision ID: 2026060318
Revises: 2026053018
Create Date: 2026-06-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026060318"
down_revision = "2026053018"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("question", schema=None) as batch_op:
        batch_op.add_column(sa.Column("explanation", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("question", schema=None) as batch_op:
        batch_op.drop_column("explanation")
