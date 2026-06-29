"""Procurement enhancement for ship repair modules: add source_type, spare_part_risk_id and other ship repair related fields

Revision ID: 006_procurement_ship_repair_enhancement
Revises: 005_ship_repair_modules
Create Date: 2026-05-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '006_procurement_ship_repair_enhancement'
down_revision: Union[str, None] = '005_ship_repair_modules'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================== 增强采购单表，支持修船模块 ====================
    # 添加 source_type 列
    op.add_column(
        'procurements',
        sa.Column('source_type', sa.String(50), nullable=True, server_default='NORMAL')
    )
    # 添加 spare_part_risk_id 列
    op.add_column(
        'procurements',
        sa.Column('spare_part_risk_id', sa.Integer(), sa.ForeignKey('spare_part_risks.id'), nullable=True)
    )
    # 添加 repair_task_id 列
    op.add_column(
        'procurements',
        sa.Column('repair_task_id', sa.Integer(), sa.ForeignKey('repair_tasks.id'), nullable=True)
    )
    # 添加 affects_schedule 列
    op.add_column(
        'procurements',
        sa.Column('affects_schedule', sa.Boolean(), nullable=False, server_default='false')
    )
    # 添加 risk_resolved 列
    op.add_column(
        'procurements',
        sa.Column('risk_resolved', sa.Boolean(), nullable=False, server_default='false')
    )
    # 添加 risk_resolved_at 列
    op.add_column(
        'procurements',
        sa.Column('risk_resolved_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    # 移除新增的列
    op.drop_column('procurements', 'risk_resolved_at')
    op.drop_column('procurements', 'risk_resolved')
    op.drop_column('procurements', 'affects_schedule')
    op.drop_column('procurements', 'repair_task_id')
    op.drop_column('procurements', 'spare_part_risk_id')
    op.drop_column('procurements', 'source_type')
