"""batch archive fields

Revision ID: 2026053018
Revises: 2026021318
Create Date: 2026-05-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026053018"
down_revision = "2026021318"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("batch", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active")
        )
        batch_op.add_column(sa.Column("academic_year", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("exam_year", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("archived_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("archived_by", sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table("batch", schema=None) as batch_op:
        batch_op.drop_column("archived_by")
        batch_op.drop_column("archived_at")
        batch_op.drop_column("exam_year")
        batch_op.drop_column("academic_year")
        batch_op.drop_column("status")
