"""ISO 9001 completion: sla_deadline, collection_records

Revision ID: 004_iso_completion
Revises: 003_supplier_categories
Create Date: 2026-04-20
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_iso_completion'
down_revision: Union[str, None] = '003_supplier_categories'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sla_deadline to complaints
    op.add_column('complaints', sa.Column('sla_deadline', sa.DateTime(timezone=True), nullable=True))

    # Collection records for payment follow-up (催收记录)
    op.create_table(
        'collection_records',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('payment_plan_id', sa.Integer(), sa.ForeignKey('payment_plans.id'), nullable=False),
        sa.Column('contract_id', sa.Integer(), sa.ForeignKey('contracts.id'), nullable=False),
        sa.Column('collection_date', sa.Date(), nullable=False),
        sa.Column('method', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('collector_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('next_followup_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('collection_records')
    op.drop_column('complaints', 'sla_deadline')
