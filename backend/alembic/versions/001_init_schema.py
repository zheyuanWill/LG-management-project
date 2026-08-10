"""init_schema

Revision ID: 001
Revises: 
Create Date: 2026-08-10 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 确保 pgvector 扩展 ──────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # ── 用户表 ──────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(length=64), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(length=256), nullable=False),
        sa.Column('display_name', sa.String(length=128), nullable=True),
        sa.Column('role', sa.String(length=20), server_default='user', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 客户表 ──────────────────────────────────
    op.create_table(
        'customers',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('contact_person', sa.String(length=128), nullable=True),
        sa.Column('phone', sa.String(length=32), nullable=True),
        sa.Column('survey_conclusion', sa.String(length=20), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 项目表 ──────────────────────────────────
    op.create_table(
        'projects',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_no', sa.String(length=32), unique=True, nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('ship_name', sa.String(length=128), nullable=False),
        sa.Column('imo', sa.String(length=16), nullable=True),
        sa.Column('owner_id', sa.BigInteger(), sa.ForeignKey('customers.id'), nullable=True),
        sa.Column('planned_completion_date', sa.Date(), nullable=True),
        sa.Column('actual_completion_date', sa.Date(), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_projects_type', 'projects', ['type'])
    op.create_index('ix_projects_status', 'projects', ['status'])

    # ── 任务表 ──────────────────────────────────
    op.create_table(
        'tasks',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=512), nullable=False),
        sa.Column('planned_end_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='not_started', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_tasks_project', 'tasks', ['project_id'])

    # ── 每日更新表 ──────────────────────────────
    op.create_table(
        'task_daily_updates',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.BigInteger(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('update_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('audio_duration', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('task_id', 'update_date'),
    )
    op.create_index('ix_updates_date', 'task_daily_updates', ['update_date'])

    # ── 照片表 ──────────────────────────────────
    op.create_table(
        'task_photos',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('update_id', sa.BigInteger(), sa.ForeignKey('task_daily_updates.id', ondelete='CASCADE'), nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 日报表 ──────────────────────────────────
    op.create_table(
        'daily_reports',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_date', sa.Date(), nullable=False),
        sa.Column('completed_items', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('tomorrow_plan', sa.Text(), nullable=True),
        sa.Column('risk_alert', sa.Text(), nullable=True),
        sa.Column('confirmed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('project_id', 'report_date'),
    )
    op.create_index('ix_daily_reports_project', 'daily_reports', ['project_id'])

    # ── 周报表 ──────────────────────────────────
    op.create_table(
        'weekly_reports',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('week_start_date', sa.Date(), nullable=False),
        sa.Column('week_end_date', sa.Date(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('next_week_plan', sa.Text(), nullable=False),
        sa.Column('confirmed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('confirmed_by', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('project_id', 'week_start_date'),
    )

    # ── 风险事件表 ──────────────────────────────
    op.create_table(
        'risk_events',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('risk_level', sa.String(length=20), server_default='info', nullable=False),
        sa.Column('resolved', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_risk_project', 'risk_events', ['project_id'])

    # ── 项目完工资料 ────────────────────────────
    op.create_table(
        'project_completions',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('completion_cert_key', sa.String(length=512), nullable=True),
        sa.Column('acceptance_cert_key', sa.String(length=512), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 经纪: 背景调研 ──────────────────────────
    op.create_table(
        'brokerage_surveys',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('conclusion', sa.String(length=20), nullable=True),
        sa.Column('survey_detail', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 经纪: 商务结果 ──────────────────────────
    op.create_table(
        'brokerage_commercials',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('quote_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('commission_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('payment_status', sa.String(length=20), server_default='unpaid', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 经纪: 合同 ──────────────────────────────
    op.create_table(
        'brokerage_contracts',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('moa_file_key', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 修船经纪 ────────────────────────────────
    op.create_table(
        'repair_brokerages',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('shipyard_quote', sa.Numeric(12, 2), nullable=True),
        sa.Column('contract_file_key', sa.String(length=512), nullable=True),
        sa.Column('handed_over', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('handed_over_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 备件: 信息 ──────────────────────────────
    op.create_table(
        'spare_part_details',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('item_name', sa.String(length=256), nullable=False),
        sa.Column('model_or_drawing', sa.String(length=256), nullable=True),
        sa.Column('quantity', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 备件: 发货照片 ──────────────────────────
    op.create_table(
        'spare_part_photos',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('photo_type', sa.String(length=32), nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 物流节点 ────────────────────────────────
    op.create_table(
        'logistics_nodes',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('node_type', sa.String(length=32), nullable=False),
        sa.Column('node_date', sa.Date(), nullable=False),
        sa.Column('tracking_no', sa.String(length=128), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('attachment_key', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_logistics_project', 'logistics_nodes', ['project_id'])

    # ── 香港签收单 ──────────────────────────────
    op.create_table(
        'hk_signatures',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('signature_file_key', sa.String(length=512), nullable=True),
        sa.Column('signed_at', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 发票 ────────────────────────────────────
    op.create_table(
        'invoices',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('title', sa.String(length=256), nullable=True),
        sa.Column('tax_number', sa.String(length=64), nullable=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('purpose', sa.String(length=256), server_default='用于出口退税', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 随手存 ──────────────────────────────────
    op.create_table(
        'quick_saves',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('content_type', sa.String(length=20), nullable=False),
        sa.Column('content_text', sa.Text(), nullable=True),
        sa.Column('file_key', sa.String(length=512), nullable=True),
        sa.Column('recognized_text', sa.Text(), nullable=True),
        sa.Column('suggested_project_id', sa.BigInteger(), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('confirmed_project_id', sa.BigInteger(), sa.ForeignKey('projects.id'), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_quick_saves_status', 'quick_saves', ['status'])

    # ── 知识库文档 ──────────────────────────────
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=True),
        sa.Column('file_key', sa.String(length=512), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=True),
        sa.Column('uploaded_by', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ── 知识库嵌入 ──────────────────────────────
    op.create_table(
        'knowledge_embeddings',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('document_id', sa.BigInteger(), sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('embedding', pgvector.Vector(512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_embeddings_document', 'knowledge_embeddings', ['document_id'])

    # ── 文件中心 ────────────────────────────────
    op.create_table(
        'files',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('project_id', sa.BigInteger(), sa.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True),
        sa.Column('file_name', sa.String(length=256), nullable=False),
        sa.Column('file_type', sa.String(length=64), nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.String(length=128), nullable=True),
        sa.Column('uploaded_by', sa.BigInteger(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_files_project', 'files', ['project_id'])
    op.create_index('ix_files_type', 'files', ['file_type'])


def downgrade() -> None:
    op.drop_table('files')
    op.drop_table('knowledge_embeddings')
    op.drop_table('knowledge_documents')
    op.drop_table('quick_saves')
    op.drop_table('invoices')
    op.drop_table('hk_signatures')
    op.drop_table('logistics_nodes')
    op.drop_table('spare_part_photos')
    op.drop_table('spare_part_details')
    op.drop_table('repair_brokerages')
    op.drop_table('brokerage_contracts')
    op.drop_table('brokerage_commercials')
    op.drop_table('brokerage_surveys')
    op.drop_table('project_completions')
    op.drop_table('risk_events')
    op.drop_table('weekly_reports')
    op.drop_table('daily_reports')
    op.drop_table('task_photos')
    op.drop_table('task_daily_updates')
    op.drop_table('tasks')
    op.drop_table('projects')
    op.drop_table('customers')
    op.drop_table('users')