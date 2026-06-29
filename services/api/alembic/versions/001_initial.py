"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2026-01-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('hashed_password', sa.String(128), nullable=False),
        sa.Column('real_name', sa.String(100), nullable=True),
        sa.Column('role', sa.Enum('OWNER', 'PM', 'PROC', 'FIN', 'OPS', name='userrole', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'])
    op.create_index(op.f('ix_users_email'), 'users', ['email'])

    # Customers
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('contact_person', sa.String(100), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('contact_email', sa.String(200), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_customers_code'), 'customers', ['code'])

    # Vessels
    op.create_table(
        'vessels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('imo_number', sa.String(50), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('vessel_type', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'])
    )

    # Suppliers
    op.create_table(
        'suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('type', sa.Enum('GOODS', 'SERVICE', name='suppliertype', create_type=False), nullable=False),
        sa.Column('contact_person', sa.String(100), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('contact_email', sa.String(200), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('bank_account', sa.String(100), nullable=True),
        sa.Column('bank_name', sa.String(200), nullable=True),
        sa.Column('tax_id', sa.String(50), nullable=True),
        sa.Column('is_preferred', sa.Boolean(), default=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_suppliers_code'), 'suppliers', ['code'])

    # Products
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(500), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('specification', sa.String(500), nullable=True),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('brand', sa.String(200), nullable=True),
        sa.Column('hs_code', sa.String(20), nullable=True),
        sa.Column('tax_refund_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('shelf_life', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_products_code'), 'products', ['code'])

    # Supplier Quotes
    op.create_table(
        'supplier_quotes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('min_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('lead_time', sa.Integer(), nullable=True),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('is_preferred', sa.Boolean(), default=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )

    # Orders
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_no', sa.String(50), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('vessel_id', sa.Integer(), nullable=True),
        sa.Column('project_type', sa.Enum('TECHNICAL_SERVICE', 'SUPERVISION', 'SPARE_PARTS', 'IMPORT_EXPORT_AGENT', 'BROKERAGE', 'AGENCY_FEE', name='projecttype', create_type=False), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', name='orderstatus', create_type=False), default='DRAFT'),
        sa.Column('currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('total_amount', sa.Numeric(18, 2), default=0),
        sa.Column('delivery_date', sa.Date(), nullable=True),
        sa.Column('pm_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_no'),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
        sa.ForeignKeyConstraint(['vessel_id'], ['vessels.id']),
        sa.ForeignKeyConstraint(['pm_id'], ['users.id'])
    )
    op.create_index(op.f('ix_orders_order_no'), 'orders', ['order_no'])

    # Order Line Items
    op.create_table(
        'order_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('product_name', sa.String(500), nullable=False),
        sa.Column('specification', sa.String(500), nullable=True),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )

    # Quotes
    op.create_table(
        'quotes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quote_no', sa.String(50), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('status', sa.Enum('DRAFT', 'SENT', 'FEEDBACK', 'ACCEPTED', 'REJECTED', name='quotestatus', create_type=False), default='DRAFT'),
        sa.Column('currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('total_amount', sa.Numeric(18, 2), default=0),
        sa.Column('valid_until', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('quote_no'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'])
    )
    op.create_index(op.f('ix_quotes_quote_no'), 'quotes', ['quote_no'])

    # Quote Line Items
    op.create_table(
        'quote_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('quote_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=True),
        sa.Column('product_name', sa.String(500), nullable=False),
        sa.Column('specification', sa.String(500), nullable=True),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['quote_id'], ['quotes.id'])
    )

    # Contracts
    op.create_table(
        'contracts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_no', sa.String(50), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('quote_id', sa.Integer(), nullable=True),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING_APPROVAL', 'EFFECTIVE', 'EXECUTING', 'COMPLETED', 'TERMINATED', name='contractstatus', create_type=False), default='DRAFT'),
        sa.Column('currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('total_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('signed_date', sa.Date(), nullable=True),
        sa.Column('effective_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('payment_terms', sa.Text(), nullable=True),
        sa.Column('delivery_terms', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('contract_no'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['quote_id'], ['quotes.id']),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'])
    )
    op.create_index(op.f('ix_contracts_contract_no'), 'contracts', ['contract_no'])

    # Payment Plans
    op.create_table(
        'payment_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('phase', sa.String(100), nullable=False),
        sa.Column('percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('planned_amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('planned_date', sa.Date(), nullable=False),
        sa.Column('actual_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('actual_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id'])
    )

    # Payment Records
    op.create_table(
        'payment_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('amount_cny', sa.Numeric(18, 2), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_method', sa.String(100), nullable=True),
        sa.Column('bank_account', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'])
    )

    # Procurements
    op.create_table(
        'procurements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('procurement_no', sa.String(50), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'ORDERED', 'PARTIAL_RECEIVED', 'RECEIVED', 'CANCELLED', name='procurementstatus', create_type=False), default='DRAFT'),
        sa.Column('currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('total_amount', sa.Numeric(18, 2), default=0),
        sa.Column('expected_date', sa.Date(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('procurement_no'),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'])
    )
    op.create_index(op.f('ix_procurements_procurement_no'), 'procurements', ['procurement_no'])

    # Procurement Line Items
    op.create_table(
        'procurement_line_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('procurement_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('product_name', sa.String(500), nullable=False),
        sa.Column('specification', sa.String(500), nullable=True),
        sa.Column('unit', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 4), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('received_quantity', sa.Numeric(18, 4), default=0),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['procurement_id'], ['procurements.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )

    # Disbursements
    op.create_table(
        'disbursements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('procurement_id', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('amount_cny', sa.Numeric(18, 2), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_method', sa.String(100), nullable=True),
        sa.Column('invoice_no', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['procurement_id'], ['procurements.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['supplier_id'], ['suppliers.id'])
    )

    # Inventory Batches
    op.create_table(
        'inventory_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('batch_no', sa.String(50), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('reserved_quantity', sa.Numeric(18, 4), default=0),
        sa.Column('unit_cost', sa.Numeric(18, 4), nullable=False),
        sa.Column('currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('procurement_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['procurement_id'], ['procurements.id'])
    )
    op.create_index(op.f('ix_inventory_batches_batch_no'), 'inventory_batches', ['batch_no'])

    # Inventory Movements
    op.create_table(
        'inventory_movements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.Enum('IN', 'OUT', 'RESERVE', 'RELEASE', 'ADJUST', name='inventorymovementtype', create_type=False), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('procurement_id', sa.Integer(), nullable=True),
        sa.Column('operator_id', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.ForeignKeyConstraint(['batch_id'], ['inventory_batches.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['procurement_id'], ['procurements.id']),
        sa.ForeignKeyConstraint(['operator_id'], ['users.id'])
    )

    # Inventory Reservations
    op.create_table(
        'inventory_reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['batch_id'], ['inventory_batches.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'])
    )

    # Node Templates
    op.create_table(
        'node_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('project_type', sa.Enum('TECHNICAL_SERVICE', 'SUPERVISION', 'SPARE_PARTS', 'IMPORT_EXPORT_AGENT', 'BROKERAGE', 'AGENCY_FEE', name='projecttype', create_type=False), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('default_days', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_required', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Tracking Nodes
    op.create_table(
        'tracking_nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE', 'SKIPPED', name='nodestatus', create_type=False), default='PENDING'),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('planned_date', sa.Date(), nullable=True),
        sa.Column('actual_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['template_id'], ['node_templates.id']),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'])
    )

    # Cost Categories
    op.create_table(
        'cost_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['parent_id'], ['cost_categories.id'])
    )

    # Exchange Rates
    op.create_table(
        'exchange_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), nullable=False),
        sa.Column('to_currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), nullable=False),
        sa.Column('rate', sa.Numeric(18, 6), nullable=False),
        sa.Column('effective_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Settlements
    op.create_table(
        'settlements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('settlement_no', sa.String(50), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PENDING_APPROVAL', 'APPROVING', 'APPROVED', 'REJECTED', 'COMPLETED', name='settlementstatus', create_type=False), default='DRAFT'),
        sa.Column('total_revenue', sa.Numeric(18, 2), default=0),
        sa.Column('revenue_currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('total_revenue_cny', sa.Numeric(18, 2), default=0),
        sa.Column('total_cost', sa.Numeric(18, 2), default=0),
        sa.Column('cost_currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('total_cost_cny', sa.Numeric(18, 2), default=0),
        sa.Column('total_received', sa.Numeric(18, 2), default=0),
        sa.Column('received_percentage', sa.Numeric(5, 2), default=0),
        sa.Column('total_disbursed', sa.Numeric(18, 2), default=0),
        sa.Column('pending_disbursement', sa.Numeric(18, 2), default=0),
        sa.Column('gross_profit', sa.Numeric(18, 2), default=0),
        sa.Column('gross_profit_rate', sa.Numeric(5, 2), default=0),
        sa.Column('applicant_id', sa.Integer(), nullable=False),
        sa.Column('apply_date', sa.Date(), nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=True),
        sa.Column('approve_date', sa.Date(), nullable=True),
        sa.Column('reject_reason', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('settlement_no'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['contract_id'], ['contracts.id']),
        sa.ForeignKeyConstraint(['applicant_id'], ['users.id']),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'])
    )
    op.create_index(op.f('ix_settlements_settlement_no'), 'settlements', ['settlement_no'])

    # Cost Items
    op.create_table(
        'cost_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('settlement_id', sa.Integer(), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('amount', sa.Numeric(18, 2), nullable=False),
        sa.Column('currency', sa.Enum('CNY', 'USD', 'EUR', 'JPY', 'HKD', name='currency', create_type=False), default='CNY'),
        sa.Column('amount_cny', sa.Numeric(18, 2), nullable=False),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=True),
        sa.Column('tax_amount', sa.Numeric(18, 2), nullable=True),
        sa.Column('invoice_no', sa.String(100), nullable=True),
        sa.Column('invoice_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['settlement_id'], ['settlements.id']),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id']),
        sa.ForeignKeyConstraint(['category_id'], ['cost_categories.id'])
    )

    # File Attachments
    op.create_table(
        'file_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('original_name', sa.String(500), nullable=False),
        sa.Column('file_key', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(200), nullable=False),
        sa.Column('size', sa.Integer(), nullable=False),
        sa.Column('sha1', sa.String(40), nullable=True),
        sa.Column('object_type', sa.Enum('ORDER', 'QUOTE', 'CONTRACT', 'PROCUREMENT', 'TRACKING_NODE', 'SETTLEMENT', 'INVOICE', 'BILL_OF_LADING', 'ACCEPTANCE', 'PHOTO', 'OTHER', name='fileobjecttype', create_type=False), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=False),
        sa.Column('uploader_id', sa.Integer(), nullable=False),
        sa.Column('thumbnail_key', sa.String(500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('file_key'),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'])
    )
    op.create_index(op.f('ix_file_attachments_object_id'), 'file_attachments', ['object_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_file_attachments_object_id'), table_name='file_attachments')
    op.drop_table('file_attachments')
    op.drop_table('cost_items')
    op.drop_index(op.f('ix_settlements_settlement_no'), table_name='settlements')
    op.drop_table('settlements')
    op.drop_table('exchange_rates')
    op.drop_table('cost_categories')
    op.drop_table('tracking_nodes')
    op.drop_table('node_templates')
    op.drop_table('inventory_reservations')
    op.drop_table('inventory_movements')
    op.drop_index(op.f('ix_inventory_batches_batch_no'), table_name='inventory_batches')
    op.drop_table('inventory_batches')
    op.drop_table('disbursements')
    op.drop_table('procurement_line_items')
    op.drop_index(op.f('ix_procurements_procurement_no'), table_name='procurements')
    op.drop_table('procurements')
    op.drop_table('payment_records')
    op.drop_table('payment_plans')
    op.drop_index(op.f('ix_contracts_contract_no'), table_name='contracts')
    op.drop_table('contracts')
    op.drop_table('quote_line_items')
    op.drop_index(op.f('ix_quotes_quote_no'), table_name='quotes')
    op.drop_table('quotes')
    op.drop_table('order_line_items')
    op.drop_index(op.f('ix_orders_order_no'), table_name='orders')
    op.drop_table('orders')
    op.drop_table('supplier_quotes')
    op.drop_index(op.f('ix_products_code'), table_name='products')
    op.drop_table('products')
    op.drop_index(op.f('ix_suppliers_code'), table_name='suppliers')
    op.drop_table('suppliers')
    op.drop_table('vessels')
    op.drop_index(op.f('ix_customers_code'), table_name='customers')
    op.drop_table('customers')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
    
    # Drop ENUMs
    op.execute("DROP TYPE IF EXISTS fileobjecttype")
    op.execute("DROP TYPE IF EXISTS settlementstatus")
    op.execute("DROP TYPE IF EXISTS nodestatus")
    op.execute("DROP TYPE IF EXISTS inventorymovementtype")
    op.execute("DROP TYPE IF EXISTS procurementstatus")
    op.execute("DROP TYPE IF EXISTS contractstatus")
    op.execute("DROP TYPE IF EXISTS quotestatus")
    op.execute("DROP TYPE IF EXISTS orderstatus")
    op.execute("DROP TYPE IF EXISTS projecttype")
    op.execute("DROP TYPE IF EXISTS suppliertype")
    op.execute("DROP TYPE IF EXISTS currency")
    op.execute("DROP TYPE IF EXISTS userrole")

