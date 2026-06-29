"""ISO 9001 process tables and column additions

Revision ID: 002_iso9001
Revises: 001_initial
Create Date: 2026-04-14
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_iso9001'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    enum_defs = [
        ("risklevel", "'HIGH', 'MEDIUM', 'LOW'"),
        ("approvalstatus", "'PENDING', 'APPROVED', 'REJECTED'"),
        ("inquirymethod", "'EMAIL', 'PHONE', 'CHAT'"),
        ("inspectionresult", "'PASS', 'FAIL', 'CONDITIONAL'"),
        ("complaintstatus", "'RECEIVED', 'INVESTIGATING', 'RESOLVED', 'CLOSED'"),
        ("surveystatus", "'DRAFT', 'SENT', 'RESPONDED', 'CLOSED'"),
        ("evaluationlevel", "'EXCELLENT', 'QUALIFIED', 'OBSERVED', 'ELIMINATED'"),
        ("changetype", "'REQUIREMENT', 'PRICE', 'SCHEDULE', 'SCOPE'"),
        ("closurestatus", "'DRAFT', 'PENDING', 'APPROVED', 'CLOSED'"),
    ]
    for name, values in enum_defs:
        op.execute(sa.text(
            f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({values}); "
            f"EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
        ))

    risk_level = sa.Enum('HIGH', 'MEDIUM', 'LOW', name='risklevel', create_type=False)
    approval_status = sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='approvalstatus', create_type=False)
    inquiry_method = sa.Enum('EMAIL', 'PHONE', 'CHAT', name='inquirymethod', create_type=False)
    inspection_result = sa.Enum('PASS', 'FAIL', 'CONDITIONAL', name='inspectionresult', create_type=False)
    complaint_status = sa.Enum('RECEIVED', 'INVESTIGATING', 'RESOLVED', 'CLOSED', name='complaintstatus', create_type=False)
    survey_status = sa.Enum('DRAFT', 'SENT', 'RESPONDED', 'CLOSED', name='surveystatus', create_type=False)
    evaluation_level = sa.Enum('EXCELLENT', 'QUALIFIED', 'OBSERVED', 'ELIMINATED', name='evaluationlevel', create_type=False)
    change_type = sa.Enum('REQUIREMENT', 'PRICE', 'SCHEDULE', 'SCOPE', name='changetype', create_type=False)
    closure_status = sa.Enum('DRAFT', 'PENDING', 'APPROVED', 'CLOSED', name='closurestatus', create_type=False)

    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'INQUIRY' BEFORE 'DRAFT'")

    for v in ['RISK_ASSESSMENT', 'CONTRACT_REVIEW', 'QUALITY_INSPECTION', 'PROJECT_CHANGE',
              'PROJECT_CLOSURE', 'COMPLAINT', 'SUPPLIER_ADMISSION', 'KNOWLEDGE']:
        op.execute(f"ALTER TYPE fileobjecttype ADD VALUE IF NOT EXISTS '{v}'")

    # --- Add columns to existing tables ---
    op.add_column('orders', sa.Column('inquiry_no', sa.String(50), unique=True))
    op.add_column('orders', sa.Column('project_code', sa.String(50), unique=True))
    op.add_column('orders', sa.Column('inquiry_source', sa.String(50)))
    op.add_column('orders', sa.Column('risk_level', sa.String(10)))
    op.add_column('orders', sa.Column('cancellation_reason', sa.Text()))
    op.add_column('orders', sa.Column('cancellation_category', sa.String(50)))
    op.create_index('ix_orders_inquiry_no', 'orders', ['inquiry_no'], unique=True)
    op.create_index('ix_orders_project_code', 'orders', ['project_code'], unique=True)

    op.add_column('suppliers', sa.Column('qualification_status', sa.String(20), server_default='QUALIFIED'))
    op.add_column('suppliers', sa.Column('business_license', sa.String(200)))
    op.add_column('suppliers', sa.Column('industry_qualification', sa.Text()))
    op.add_column('suppliers', sa.Column('admission_date', sa.Date()))
    op.add_column('suppliers', sa.Column('last_evaluation_date', sa.Date()))
    op.add_column('suppliers', sa.Column('evaluation_score', sa.Numeric(5, 2)))
    op.add_column('suppliers', sa.Column('evaluation_level', sa.String(20)))

    op.add_column('contracts', sa.Column('warranty_period', sa.Integer()))
    op.add_column('contracts', sa.Column('warranty_end_date', sa.Date()))
    op.add_column('contracts', sa.Column('contract_type', sa.String(20), server_default='customer'))
    op.add_column('contracts', sa.Column('related_contract_id', sa.Integer(), sa.ForeignKey('contracts.id')))

    # --- New tables ---
    op.create_table('number_sequences',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('prefix', sa.String(30), nullable=False),
        sa.Column('current_value', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('prefix', name='uq_number_sequences_prefix'),
    )

    op.create_table('inquiry_risk_assessments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('customer_credit', risk_level),
        sa.Column('project_feasibility', risk_level),
        sa.Column('payment_risk', risk_level),
        sa.Column('overall_risk', risk_level),
        sa.Column('assessment_notes', sa.Text()),
        sa.Column('assessor_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('status', approval_status, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('inquiry_records',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('inquiry_method', inquiry_method, server_default='EMAIL'),
        sa.Column('inquiry_time', sa.DateTime(timezone=True)),
        sa.Column('deadline', sa.DateTime(timezone=True)),
        sa.Column('responded', sa.Boolean(), server_default='false'),
        sa.Column('response_time', sa.DateTime(timezone=True)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('supplier_comparisons',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('title', sa.String(200)),
        sa.Column('selected_supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id')),
        sa.Column('selection_reason', sa.Text()),
        sa.Column('comparison_data', sa.JSON()),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('contract_reviews',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('contract_id', sa.Integer(), sa.ForeignKey('contracts.id'), nullable=False),
        sa.Column('delivery_review', sa.Text()),
        sa.Column('payment_review', sa.Text()),
        sa.Column('technical_review', sa.Text()),
        sa.Column('penalty_review', sa.Text()),
        sa.Column('warranty_review', sa.Text()),
        sa.Column('conclusion', sa.String(20), server_default='PENDING'),
        sa.Column('reviewers', sa.JSON()),
        sa.Column('review_date', sa.Date()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('project_changes',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('change_no', sa.String(50), unique=True, nullable=False),
        sa.Column('change_type', change_type, nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('impact_analysis', sa.Text()),
        sa.Column('customer_confirmation', sa.Boolean(), server_default='false'),
        sa.Column('confirmation_date', sa.Date()),
        sa.Column('confirmation_file_id', sa.Integer()),
        sa.Column('status', approval_status, server_default='PENDING'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('quality_inspections',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('procurement_id', sa.Integer(), sa.ForeignKey('procurements.id')),
        sa.Column('inspection_type', sa.String(50), nullable=False),
        sa.Column('inspection_date', sa.Date()),
        sa.Column('result', inspection_result),
        sa.Column('inspector_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('findings', sa.Text()),
        sa.Column('report_data', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('project_acceptances',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False),
        sa.Column('acceptance_no', sa.String(50), unique=True, nullable=False),
        sa.Column('acceptance_type', sa.String(20), nullable=False),
        sa.Column('acceptance_date', sa.Date()),
        sa.Column('customer_confirmed', sa.Boolean(), server_default='false'),
        sa.Column('confirmation_method', sa.String(20)),
        sa.Column('confirmation_date', sa.Date()),
        sa.Column('notes', sa.Text()),
        sa.Column('status', sa.String(20), server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('project_closures',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id'), nullable=False, unique=True),
        sa.Column('closure_no', sa.String(50), unique=True, nullable=False),
        sa.Column('all_payments_settled', sa.Boolean(), server_default='false'),
        sa.Column('all_receivables_collected', sa.Boolean(), server_default='false'),
        sa.Column('documents_archived', sa.Boolean(), server_default='false'),
        sa.Column('archive_location', sa.String(200)),
        sa.Column('lessons_learned', sa.Text()),
        sa.Column('improvement_suggestions', sa.Text()),
        sa.Column('closed_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('closed_at', sa.DateTime(timezone=True)),
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('status', closure_status, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('complaints',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('complaint_no', sa.String(50), unique=True, nullable=False),
        sa.Column('order_id', sa.Integer(), sa.ForeignKey('orders.id')),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('source', inquiry_method, server_default='EMAIL'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('responded_at', sa.DateTime(timezone=True)),
        sa.Column('investigation', sa.Text()),
        sa.Column('resolution', sa.Text()),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('customer_feedback', sa.Text()),
        sa.Column('handler_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('status', complaint_status, server_default='RECEIVED'),
        sa.Column('period_no_complaint', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('satisfaction_surveys',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('survey_no', sa.String(50), unique=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('service_quality', sa.Integer()),
        sa.Column('response_speed', sa.Integer()),
        sa.Column('price_reasonability', sa.Integer()),
        sa.Column('communication', sa.Integer()),
        sa.Column('overall_satisfaction', sa.Integer()),
        sa.Column('comments', sa.Text()),
        sa.Column('sent_at', sa.DateTime(timezone=True)),
        sa.Column('responded_at', sa.DateTime(timezone=True)),
        sa.Column('status', survey_status, server_default='DRAFT'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('supplier_admissions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('business_license_verified', sa.Boolean(), server_default='false'),
        sa.Column('industry_qualification_verified', sa.Boolean(), server_default='false'),
        sa.Column('case_references', sa.Text()),
        sa.Column('trial_evaluation', sa.Text()),
        sa.Column('trial_result', sa.String(20)),
        sa.Column('approval_status', approval_status, server_default='PENDING'),
        sa.Column('approved_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('approved_at', sa.DateTime(timezone=True)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('supplier_evaluations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id'), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('quality_score', sa.Numeric(5, 2)),
        sa.Column('delivery_score', sa.Numeric(5, 2)),
        sa.Column('price_score', sa.Numeric(5, 2)),
        sa.Column('service_score', sa.Numeric(5, 2)),
        sa.Column('total_score', sa.Numeric(5, 2)),
        sa.Column('level', evaluation_level),
        sa.Column('evaluator_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('evaluation_date', sa.Date()),
        sa.Column('notified_supplier', sa.Boolean(), server_default='false'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('change_logs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=False),
        sa.Column('change_content', sa.JSON()),
        sa.Column('changed_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('version_before', sa.String(10)),
        sa.Column('version_after', sa.String(10)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_change_logs_entity', 'change_logs', ['entity_type', 'entity_id'])

    op.create_table('knowledge_documents',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text()),
        sa.Column('doc_type', sa.String(50), nullable=False),
        sa.Column('source_type', sa.String(50)),
        sa.Column('source_id', sa.Integer()),
        sa.Column('file_id', sa.Integer()),
        sa.Column('embedding_status', sa.String(20), server_default='pending'),
        sa.Column('tags', sa.JSON()),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table('knowledge_chunks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.Text()),
        sa.Column('metadata_json', sa.JSON()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('knowledge_chunks')
    op.drop_table('knowledge_documents')
    op.drop_table('change_logs')
    op.drop_table('supplier_evaluations')
    op.drop_table('supplier_admissions')
    op.drop_table('satisfaction_surveys')
    op.drop_table('complaints')
    op.drop_table('project_closures')
    op.drop_table('project_acceptances')
    op.drop_table('quality_inspections')
    op.drop_table('project_changes')
    op.drop_table('contract_reviews')
    op.drop_table('supplier_comparisons')
    op.drop_table('inquiry_records')
    op.drop_table('inquiry_risk_assessments')
    op.drop_table('number_sequences')

    op.drop_column('contracts', 'related_contract_id')
    op.drop_column('contracts', 'contract_type')
    op.drop_column('contracts', 'warranty_end_date')
    op.drop_column('contracts', 'warranty_period')

    op.drop_column('suppliers', 'evaluation_level')
    op.drop_column('suppliers', 'evaluation_score')
    op.drop_column('suppliers', 'last_evaluation_date')
    op.drop_column('suppliers', 'admission_date')
    op.drop_column('suppliers', 'industry_qualification')
    op.drop_column('suppliers', 'business_license')
    op.drop_column('suppliers', 'qualification_status')

    op.drop_index('ix_orders_project_code', 'orders')
    op.drop_index('ix_orders_inquiry_no', 'orders')
    op.drop_column('orders', 'cancellation_category')
    op.drop_column('orders', 'cancellation_reason')
    op.drop_column('orders', 'risk_level')
    op.drop_column('orders', 'inquiry_source')
    op.drop_column('orders', 'project_code')
    op.drop_column('orders', 'inquiry_no')

    for name in ['closurestatus', 'changetype', 'evaluationlevel', 'surveystatus',
                 'complaintstatus', 'inspectionresult', 'inquirymethod',
                 'approvalstatus', 'risklevel']:
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
