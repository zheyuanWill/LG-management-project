"""Ship repair modules: customer visit, background check, inquiries, plans, daily reports, anomalies, NCRs, spare part risks, reviews

Revision ID: 005_ship_repair_modules
Revises: 004_iso_completion
Create Date: 2026-05-28
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '005_ship_repair_modules'
down_revision: Union[str, None] = '004_iso_completion'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ==================== 客户回访 ====================
    op.create_table(
        'customer_visits',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('visit_type', sa.String(50), nullable=False),
        sa.Column('visit_date', sa.Date(), nullable=False),
        sa.Column('visit_leader_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('contact_person', sa.String(200), nullable=True),
        sa.Column('contact_method', sa.String(50), nullable=False),
        sa.Column('current_fleet_status', sa.Text(), nullable=True),
        sa.Column('potential_repair_demand', sa.Text(), nullable=True),
        sa.Column('expected_docking_date', sa.Date(), nullable=True),
        sa.Column('customer_key_concerns', sa.Text(), nullable=True),
        sa.Column('past_project_feedback', sa.Text(), nullable=True),
        sa.Column('customer_satisfaction', sa.String(50), nullable=False),
        sa.Column('next_followup_date', sa.Date(), nullable=True),
        sa.Column('convert_to_lead', sa.Boolean(), default=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), default='DRAFT'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 船东背调 ====================
    op.create_table(
        'shipowner_background_checks',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('check_date', sa.Date(), nullable=False),
        sa.Column('checker_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('shipowner_basic_info', sa.Text(), nullable=True),
        sa.Column('credit_payment_history', sa.Text(), nullable=True),
        sa.Column('past_cooperation_history', sa.Text(), nullable=True),
        sa.Column('contract_performance', sa.Text(), nullable=True),
        sa.Column('historical_disputes_risk_notes', sa.Text(), nullable=True),
        sa.Column('vessel_technical_status_notes', sa.Text(), nullable=True),
        sa.Column('classification_society_info', sa.Text(), nullable=True),
        sa.Column('insurance_info', sa.Text(), nullable=True),
        sa.Column('market_reputation_risk_notes', sa.Text(), nullable=True),
        sa.Column('cooperation_conclusion', sa.String(50), nullable=False),
        sa.Column('gm_approval_opinion', sa.Text(), nullable=True),
        sa.Column('gm_approved_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('gm_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), default='DRAFT'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 船厂询价 ====================
    op.create_table(
        'shipyard_inquiries',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=True),
        sa.Column('ship_name', sa.String(200), nullable=True),
        sa.Column('shipowner_name', sa.String(200), nullable=True),
        sa.Column('repair_scope', sa.Text(), nullable=True),
        sa.Column('docking_date_requirement', sa.Date(), nullable=True),
        sa.Column('shipyard_requirements', sa.Text(), nullable=True),
        sa.Column('technical_requirements', sa.Text(), nullable=True),
        sa.Column('quote_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('inquiry_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), default='PENDING_ORGANIZE'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 船厂报价 ====================
    op.create_table(
        'shipyard_quotes',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('inquiry_id', sa.Integer(), sa.ForeignKey('shipyard_inquiries.id'), nullable=False),
        sa.Column('shipyard_name', sa.String(200), nullable=False),
        sa.Column('contact_person', sa.String(200), nullable=True),
        sa.Column('quote_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('currency', sa.String(10), default='CNY'),
        sa.Column('expected_duration_days', sa.Integer(), nullable=True),
        sa.Column('quote_valid_until', sa.Date(), nullable=True),
        sa.Column('payment_terms', sa.Text(), nullable=True),
        sa.Column('included_items', sa.Text(), nullable=True),
        sa.Column('excluded_items', sa.Text(), nullable=True),
        sa.Column('risk_notes', sa.Text(), nullable=True),
        sa.Column('entered_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('entered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_recommended', sa.Boolean(), default=False),
        sa.Column('recommendation_reason', sa.Text(), nullable=True),
        sa.Column('selected_by_gm', sa.Boolean(), default=False),
        sa.Column('gm_selection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 修船计划 ====================
    op.create_table(
        'repair_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('ai_disassembled', sa.Boolean(), default=False),
        sa.Column('ai_disassembled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('human_confirmed', sa.Boolean(), default=False),
        sa.Column('human_confirmed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('human_confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('order_id', 'version', name='uq_repair_plan_order_version'),
    )

    # ==================== 修船任务 ====================
    op.create_table(
        'repair_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('plan_id', sa.Integer(), sa.ForeignKey('repair_plans.id'), nullable=False),
        sa.Column('task_name', sa.String(500), nullable=False),
        sa.Column('subtasks', sa.JSON(), nullable=True),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('expected_duration_days', sa.Integer(), nullable=True),
        sa.Column('planned_start_date', sa.Date(), nullable=True),
        sa.Column('planned_end_date', sa.Date(), nullable=True),
        sa.Column('prerequisites', sa.Text(), nullable=True),
        sa.Column('dependent_task_ids', sa.JSON(), nullable=True),
        sa.Column('can_parallel', sa.Boolean(), default=False),
        sa.Column('is_critical_path', sa.Boolean(), default=False),
        sa.Column('linked_to_spare_parts', sa.Boolean(), default=False),
        sa.Column('responsible_party', sa.String(50), nullable=False),
        sa.Column('risk_level', sa.String(50), default='LOW'),
        sa.Column('required_photo_evidence', sa.JSON(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('order_in_plan', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 计划版本对比 ====================
    op.create_table(
        'plan_version_comparisons',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('old_plan_id', sa.Integer(), sa.ForeignKey('repair_plans.id'), nullable=False),
        sa.Column('new_plan_id', sa.Integer(), sa.ForeignKey('repair_plans.id'), nullable=False),
        sa.Column('comparison_summary', sa.Text(), nullable=True),
        sa.Column('added_tasks', sa.JSON(), nullable=True),
        sa.Column('removed_tasks', sa.JSON(), nullable=True),
        sa.Column('modified_tasks', sa.JSON(), nullable=True),
        sa.Column('duration_changes', sa.JSON(), nullable=True),
        sa.Column('date_changes', sa.JSON(), nullable=True),
        sa.Column('spare_part_changes', sa.JSON(), nullable=True),
        sa.Column('risk_changes', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 监修岗日报 ====================
    op.create_table(
        'daily_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('report_date', sa.Date(), nullable=False),
        sa.Column('reporter_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('site_status', sa.String(50), nullable=False),
        sa.Column('completed_tasks', sa.Text(), nullable=True),
        sa.Column('unfinished_tasks', sa.Text(), nullable=True),
        sa.Column('unfinished_reason', sa.String(50), nullable=True),
        sa.Column('affects_schedule', sa.Boolean(), default=False),
        sa.Column('estimated_delay_days', sa.Integer(), nullable=True),
        sa.Column('affects_quality', sa.Boolean(), default=False),
        sa.Column('affects_safety', sa.Boolean(), default=False),
        sa.Column('requires_gm_decision', sa.Boolean(), default=False),
        sa.Column('gm_decision_items', sa.Text(), nullable=True),
        sa.Column('one_line_summary', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('linked_spare_part_risk_id', sa.Integer(), sa.ForeignKey('spare_part_risks.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('order_id', 'report_date', name='uq_daily_report_order_date'),
    )

    # ==================== 照片证据 ====================
    op.create_table(
        'photo_evidences',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('file_attachment_id', sa.Integer(), sa.ForeignKey('file_attachments.id'), nullable=False),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('photo_date', sa.Date(), nullable=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('repair_tasks.id'), nullable=True),
        sa.Column('daily_report_id', sa.Integer(), sa.ForeignKey('daily_reports.id'), nullable=True),
        sa.Column('anomaly_id', sa.Integer(), sa.ForeignKey('anomalies.id'), nullable=True),
        sa.Column('ncr_id', sa.Integer(), sa.ForeignKey('ncrs.id'), nullable=True),
        sa.Column('spare_part_risk_id', sa.Integer(), sa.ForeignKey('spare_part_risks.id'), nullable=True),
        sa.Column('procurement_id', sa.Integer(), sa.ForeignKey('procurements.id'), nullable=True),
        sa.Column('tracking_node_id', sa.Integer(), sa.ForeignKey('tracking_nodes.id'), nullable=True),
        sa.Column('photo_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_report_evidence', sa.Boolean(), default=False),
        sa.Column('is_iso_record', sa.Boolean(), default=False),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 异常上报 ====================
    op.create_table(
        'anomalies',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('repair_tasks.id'), nullable=True),
        sa.Column('anomaly_type', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('impact_scope', sa.Text(), nullable=True),
        sa.Column('affects_schedule', sa.Boolean(), default=False),
        sa.Column('affects_quality', sa.Boolean(), default=False),
        sa.Column('affects_safety', sa.Boolean(), default=False),
        sa.Column('suggested_solution', sa.Text(), nullable=True),
        sa.Column('reported_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('reported_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('status', sa.String(50), default='PENDING'),
        sa.Column('converted_to_ncr_id', sa.Integer(), sa.ForeignKey('ncrs.id'), nullable=True),
        sa.Column('linked_spare_part_risk_id', sa.Integer(), sa.ForeignKey('spare_part_risks.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== NCR ====================
    op.create_table(
        'ncrs',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('ncr_number', sa.String(100), unique=True, nullable=False),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('repair_tasks.id'), nullable=True),
        sa.Column('anomaly_id', sa.Integer(), sa.ForeignKey('anomalies.id'), nullable=True),
        sa.Column('issue_description', sa.Text(), nullable=False),
        sa.Column('discovered_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('discovered_date', sa.Date(), nullable=False),
        sa.Column('responsible_party', sa.String(50), nullable=False),
        sa.Column('root_cause_analysis', sa.Text(), nullable=True),
        sa.Column('rectification_requirements', sa.Text(), nullable=True),
        sa.Column('rectification_responsible_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('planned_completion_date', sa.Date(), nullable=True),
        sa.Column('rectification_measures', sa.Text(), nullable=True),
        sa.Column('review_result', sa.Text(), nullable=True),
        sa.Column('closed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 缺备件风险单 ====================
    op.create_table(
        'spare_part_risks',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('risk_number', sa.String(100), unique=True, nullable=False),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('repair_tasks.id'), nullable=True),
        sa.Column('daily_report_id', sa.Integer(), sa.ForeignKey('daily_reports.id'), nullable=True),
        sa.Column('anomaly_id', sa.Integer(), sa.ForeignKey('anomalies.id'), nullable=True),
        sa.Column('spare_part_name', sa.String(500), nullable=False),
        sa.Column('model_specification', sa.String(500), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('belonging_equipment_system', sa.String(500), nullable=True),
        sa.Column('installation_location', sa.String(500), nullable=True),
        sa.Column('affects_schedule', sa.Boolean(), default=False),
        sa.Column('affected_task_id', sa.Integer(), sa.ForeignKey('repair_tasks.id'), nullable=True),
        sa.Column('estimated_delay_days', sa.Integer(), nullable=True),
        sa.Column('urgency', sa.String(50), default='MEDIUM'),
        sa.Column('demand_reason', sa.Text(), nullable=True),
        sa.Column('supervisor_notes', sa.Text(), nullable=True),
        sa.Column('expected_arrival_date', sa.Date(), nullable=True),
        sa.Column('submitted_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('status', sa.String(50), default='DRAFT'),
        sa.Column('gm_approval_opinion', sa.Text(), nullable=True),
        sa.Column('gm_approved_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('gm_approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('gm_review_opinion', sa.Text(), nullable=True),
        sa.Column('gm_reviewed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('gm_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('linked_procurement_id', sa.Integer(), sa.ForeignKey('procurements.id'), nullable=True),
        sa.Column('risk_resolved', sa.Boolean(), default=False),
        sa.Column('risk_resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 供应商反馈 ====================
    op.create_table(
        'supplier_feedbacks',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('spare_part_risk_id', sa.Integer(), sa.ForeignKey('spare_part_risks.id'), nullable=False),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('contact_person', sa.String(200), nullable=True),
        sa.Column('can_supply', sa.Boolean(), default=False),
        sa.Column('quoted_price', sa.Numeric(18, 2), nullable=True),
        sa.Column('currency', sa.String(10), default='CNY'),
        sa.Column('delivery_date', sa.Date(), nullable=True),
        sa.Column('payment_terms', sa.Text(), nullable=True),
        sa.Column('has_alternative', sa.Boolean(), default=False),
        sa.Column('alternative_description', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('entered_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('entered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_selected', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 供应商沟通记录 ====================
    op.create_table(
        'supplier_communications',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('spare_part_risk_id', sa.Integer(), sa.ForeignKey('spare_part_risks.id'), nullable=False),
        sa.Column('communication_method', sa.String(50), nullable=False),
        sa.Column('communication_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('communicated_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content_summary', sa.Text(), nullable=False),
        sa.Column('sent_to_supplier', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # ==================== 项目复盘 ====================
    op.create_table(
        'project_reviews',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False, unique=True),
        sa.Column('project_summary', sa.Text(), nullable=True),
        sa.Column('schedule_variance', sa.Text(), nullable=True),
        sa.Column('cost_variance', sa.Text(), nullable=True),
        sa.Column('quality_issues', sa.Text(), nullable=True),
        sa.Column('safety_issues', sa.Text(), nullable=True),
        sa.Column('spare_part_issues', sa.Text(), nullable=True),
        sa.Column('supplier_issues', sa.Text(), nullable=True),
        sa.Column('customer_feedback', sa.Text(), nullable=True),
        sa.Column('lessons_learned', sa.Text(), nullable=True),
        sa.Column('improvement_measures', sa.Text(), nullable=True),
        sa.Column('responsible_person_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('planned_completion_date', sa.Date(), nullable=True),
        sa.Column('include_in_continuous_improvement', sa.Boolean(), default=False),
        sa.Column('status', sa.String(50), default='DRAFT'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('project_reviews')
    op.drop_table('supplier_communications')
    op.drop_table('supplier_feedbacks')
    op.drop_table('spare_part_risks')
    op.drop_table('ncrs')
    op.drop_table('anomalies')
    op.drop_table('photo_evidences')
    op.drop_table('daily_reports')
    op.drop_table('plan_version_comparisons')
    op.drop_table('repair_tasks')
    op.drop_table('repair_plans')
    op.drop_table('shipyard_quotes')
    op.drop_table('shipyard_inquiries')
    op.drop_table('shipowner_background_checks')
    op.drop_table('customer_visits')
