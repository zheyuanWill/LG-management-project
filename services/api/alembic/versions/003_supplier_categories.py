"""Supplier two-level category tree and association table

Revision ID: 003_supplier_categories
Revises: 002_iso9001
Create Date: 2026-04-20
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_supplier_categories'
down_revision: Union[str, None] = '002_iso9001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'supplier_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(50), nullable=False, unique=True),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('supplier_categories.id'), nullable=True),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_supplier_categories_code', 'supplier_categories', ['code'])
    op.create_index('ix_supplier_categories_parent_id', 'supplier_categories', ['parent_id'])

    op.create_table(
        'supplier_category_links',
        sa.Column('supplier_id', sa.Integer(), sa.ForeignKey('suppliers.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('supplier_categories.id', ondelete='CASCADE'), primary_key=True),
    )

    # ------------------------------------------------------------------
    # Seed the complete two-level category tree
    # ------------------------------------------------------------------
    categories = sa.table(
        'supplier_categories',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String),
        sa.column('code', sa.String),
        sa.column('level', sa.Integer),
        sa.column('parent_id', sa.Integer),
        sa.column('sort_order', sa.Integer),
        sa.column('description', sa.String),
    )

    # ---- Level 1 (一级分类 / 服务种类) ----
    level1 = [
        {'id': 1,  'name': '备件',     'code': 'L1_SPARE_PARTS',     'level': 1, 'parent_id': None, 'sort_order': 1,  'description': '船舶备件供应'},
        {'id': 2,  'name': '货物',     'code': 'L1_GOODS',           'level': 1, 'parent_id': None, 'sort_order': 2,  'description': '一般货物/物资供应'},
        {'id': 3,  'name': '维修',     'code': 'L1_REPAIR',          'level': 1, 'parent_id': None, 'sort_order': 3,  'description': '维修保养服务'},
        {'id': 4,  'name': '检测',     'code': 'L1_INSPECTION',      'level': 1, 'parent_id': None, 'sort_order': 4,  'description': '检测检验服务'},
        {'id': 5,  'name': '技术服务', 'code': 'L1_TECH_SERVICE',    'level': 1, 'parent_id': None, 'sort_order': 5,  'description': '专业技术服务'},
        {'id': 6,  'name': '监理',     'code': 'L1_SUPERVISION',     'level': 1, 'parent_id': None, 'sort_order': 6,  'description': '工程监理服务'},
        {'id': 7,  'name': '包装',     'code': 'L1_PACKAGING',       'level': 1, 'parent_id': None, 'sort_order': 7,  'description': '包装加工服务'},
        {'id': 8,  'name': '运输',     'code': 'L1_TRANSPORT',       'level': 1, 'parent_id': None, 'sort_order': 8,  'description': '物流运输服务'},
    ]
    op.bulk_insert(categories, level1)

    # ---- Level 2 (二级分类 / 项目大类) ----
    level2 = [
        {'id': 101, 'name': '甲板舾装',     'code': 'L2_DECK_OUTFITTING',    'level': 2, 'parent_id': 1,  'sort_order': 1,  'description': '甲板舾装件、甲板机械'},
        {'id': 102, 'name': '柴油机',       'code': 'L2_DIESEL_ENGINE',      'level': 2, 'parent_id': 1,  'sort_order': 2,  'description': '主机、辅机柴油机'},
        {'id': 103, 'name': '增压器',       'code': 'L2_TURBOCHARGER',       'level': 2, 'parent_id': 1,  'sort_order': 3,  'description': '废气涡轮增压器'},
        {'id': 104, 'name': '发电机',       'code': 'L2_GENERATOR',          'level': 2, 'parent_id': 1,  'sort_order': 4,  'description': '船用发电机组'},
        {'id': 105, 'name': '锅炉',         'code': 'L2_BOILER',             'level': 2, 'parent_id': 1,  'sort_order': 5,  'description': '船用锅炉及辅机'},
        {'id': 106, 'name': '管系',         'code': 'L2_PIPING',             'level': 2, 'parent_id': 1,  'sort_order': 6,  'description': '管路系统及管件'},
        {'id': 107, 'name': '阀门',         'code': 'L2_VALVES',             'level': 2, 'parent_id': 1,  'sort_order': 7,  'description': '各类船用阀门'},
        {'id': 108, 'name': '泵类',         'code': 'L2_PUMPS',              'level': 2, 'parent_id': 1,  'sort_order': 8,  'description': '船用泵类设备'},
        {'id': 109, 'name': '液压设备',     'code': 'L2_HYDRAULIC',          'level': 2, 'parent_id': 1,  'sort_order': 9,  'description': '液压系统及元件'},
        {'id': 110, 'name': '电气设备',     'code': 'L2_ELECTRICAL',         'level': 2, 'parent_id': 1,  'sort_order': 10, 'description': '电气系统及元器件'},
        {'id': 111, 'name': '导航通信',     'code': 'L2_NAVIGATION',         'level': 2, 'parent_id': 1,  'sort_order': 11, 'description': '导航/通信/信号设备'},
        {'id': 112, 'name': '空调通风',     'code': 'L2_HVAC',               'level': 2, 'parent_id': 1,  'sort_order': 12, 'description': '空调通风制冷系统'},
        {'id': 113, 'name': '涂装防腐',     'code': 'L2_COATING',            'level': 2, 'parent_id': 1,  'sort_order': 13, 'description': '涂装、防腐、阴极保护'},
        {'id': 114, 'name': '螺旋桨推进',   'code': 'L2_PROPULSION',         'level': 2, 'parent_id': 1,  'sort_order': 14, 'description': '螺旋桨、轴系、推进系统'},
        {'id': 115, 'name': '救生消防',     'code': 'L2_LIFESAVING',         'level': 2, 'parent_id': 1,  'sort_order': 15, 'description': '救生、消防设备及系统'},
        {'id': 116, 'name': '船体结构',     'code': 'L2_HULL',               'level': 2, 'parent_id': 1,  'sort_order': 16, 'description': '船体钢结构、焊接'},
        {'id': 117, 'name': '起重设备',     'code': 'L2_CRANE',              'level': 2, 'parent_id': 1,  'sort_order': 17, 'description': '起重机、吊车、绞车'},
        {'id': 118, 'name': '压载水处理',   'code': 'L2_BALLAST_WATER',      'level': 2, 'parent_id': 1,  'sort_order': 18, 'description': '压载水管理系统'},
        {'id': 119, 'name': '脱硫系统',     'code': 'L2_SCRUBBER',           'level': 2, 'parent_id': 1,  'sort_order': 19, 'description': '废气脱硫装置'},
        {'id': 120, 'name': '锚泊系泊',     'code': 'L2_MOORING',            'level': 2, 'parent_id': 1,  'sort_order': 20, 'description': '锚、锚链、缆绳、系泊设备'},
    ]

    # 二级分类复制到每个一级分类下（每个一级都有相同的二级子项）
    all_level2 = []
    next_id = 101
    for l1 in level1:
        for i, template in enumerate(level2):
            all_level2.append({
                'id': next_id,
                'name': template['name'],
                'code': f"{l1['code']}_{template['code'].replace('L2_', '')}",
                'level': 2,
                'parent_id': l1['id'],
                'sort_order': i + 1,
                'description': template['description'],
            })
            next_id += 1

    op.bulk_insert(categories, all_level2)


def downgrade() -> None:
    op.drop_table('supplier_category_links')
    op.drop_table('supplier_categories')
