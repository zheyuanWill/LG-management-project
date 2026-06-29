"""Ship repair projects: link sr_projects to orders

Revision ID: 007_sr_project_link_order
Revises: 006_procurement_ship_repair_enhancement
Create Date: 2026-06-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '007_sr_project_link_order'
down_revision: Union[str, None] = '006_procurement_ship_repair_enhancement'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sr_projects',
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=True),
    )
    op.create_index('ix_sr_projects_order_id', 'sr_projects', ['order_id'])


def downgrade() -> None:
    op.drop_index('ix_sr_projects_order_id', table_name='sr_projects')
    op.drop_column('sr_projects', 'order_id')

