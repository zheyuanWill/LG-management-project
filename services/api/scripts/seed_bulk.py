"""
批量数据种子脚本 — 用于前端性能压测

用法:
    # 生成 10,000 条订单（默认）
    python -m scripts.seed_bulk

    # 指定数量（会按比例生成关联数据）
    python -m scripts.seed_bulk --orders 100000

    # 指定各表数量
    python -m scripts.seed_bulk --orders 50000 --products 5000 --customers 1000

    # 清除压测数据（保留基础 seed）
    python -m scripts.seed_bulk --clean

数据生成比例（以 orders 为基准）:
    customers  = orders / 50    （每客户平均 50 单）
    vessels    = customers * 2  （每客户平均 2 艘船）
    products   = orders / 20    （每 20 单约用到同一商品）
    suppliers  = products / 10
    line_items = orders * 3     （每单平均 3 个行项目）

注意: 此脚本直接用 SQLAlchemy Core 批量 INSERT，比 ORM 快 100x+。
在 i7 + SSD + PostgreSQL 上，10 万条订单约 2-3 分钟。
"""
import asyncio
import argparse
import random
import sys
import time
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal

from sqlalchemy import text, insert, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.insert(0, ".")

from app.core.config import settings
from app.db.base import Base
from app.models.user import User, UserRole
from app.models.customer import Customer, Vessel
from app.models.product import Product, Supplier, SupplierType
from app.models.order import (
    Order, OrderLineItem, ProjectType, OrderStatus, Currency
)
from app.models.notification import Notification, NotificationType


# ---------------------------------------------------------------------------
# Data Pools — realistic Chinese business data
# ---------------------------------------------------------------------------
COMPANY_NAMES = [
    "中远海运", "招商轮船", "长荣海运", "万海航运", "阳明海运", "东方海外",
    "太平船务", "以星航运", "现代商船", "海丰国际", "中外运集运", "上海锦江",
    "宁波远洋", "青岛海运", "天津海运", "大连海运", "厦门海运", "广州海运",
    "珠海港务", "南通海运", "烟台海运", "连云港船务", "湛江海运", "北海港务",
    "汕头海运", "温州海运", "福州海运", "泉州海运", "海口海运", "三亚船务",
]

VESSEL_PREFIXES = ["远洋", "海运", "长航", "明珠", "星辰", "东风", "瑞丰", "鸿运", "宝丰", "金龙"]
VESSEL_SUFFIXES = ["号", "轮", "之星", "远航", "先锋"]
VESSEL_TYPES = ["散货船", "集装箱船", "油轮", "化学品船", "滚装船", "多用途船", "LNG船"]

PRODUCT_CATEGORIES = ["发动机配件", "液压设备", "阀门", "电气设备", "涂料", "泵类", "轴承", "密封件", "过滤器", "仪器仪表"]
PRODUCT_PREFIXES = ["船用", "海洋", "工业", "高压", "低压", "精密", "标准"]
PRODUCT_NAMES = [
    "发动机缸套", "液压泵", "闸阀", "电缆", "防腐漆", "离心泵", "滚动轴承",
    "O型密封圈", "油滤器", "压力表", "温度传感器", "齿轮", "活塞环", "曲轴",
    "凸轮轴", "涡轮增压器", "散热器", "空气过滤器", "燃油喷嘴", "排气阀",
]
BRANDS = ["MAN", "博世力士乐", "上海良工", "远东电缆", "中涂", "ABB", "西门子", "SKF", "NSK", "川崎"]

SUPPLIER_NAMES = [
    "上海船舶配件", "宁波海洋设备", "青岛船舶技术", "大连机械制造", "广州重工",
    "武汉船机", "南京液压", "无锡动力", "苏州精密", "杭州泵业",
    "天津重型", "深圳电子", "珠海科技", "烟台船舶", "威海五金",
]

CONTACT_SURNAMES = "张王李赵陈刘黄周吴孙朱马胡郭林何高罗郑梁"
CONTACT_TITLES = ["经理", "主管", "工程师", "总监", "负责人"]

ORDER_NOTES_TEMPLATES = [
    "{vessel}备件采购项目",
    "{vessel}维修保养物资",
    "{vessel}年度配件补给",
    "{vessel}紧急抢修物资",
    "{vessel}坞修配套采购",
    "{vessel}航次补给",
]


def random_phone():
    return f"1{random.choice('3456789')}{random.randint(100000000, 999999999)}"


def random_contact():
    surname = random.choice(CONTACT_SURNAMES)
    title = random.choice(CONTACT_TITLES)
    return f"{surname}{title}"


def random_date_in_range(start_days_ago: int, end_days_ago: int) -> date:
    delta = random.randint(end_days_ago, start_days_ago)
    return date.today() - timedelta(days=delta)


# ---------------------------------------------------------------------------
# Batch generators
# ---------------------------------------------------------------------------
BATCH_SIZE = 5000  # rows per INSERT


def generate_customers(count: int) -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc)
    for i in range(count):
        name = f"{random.choice(COMPANY_NAMES)}{random.choice(['集团', '股份', '有限公司', '物流', '国际'])}"
        rows.append({
            "name": f"{name}-{i:06d}",
            "code": f"CUST{i:06d}",
            "contact_person": random_contact(),
            "contact_phone": random_phone(),
            "contact_email": f"contact{i}@example.com",
            "address": f"中国某省某市某区第{i}号",
            "created_at": now,
            "updated_at": now,
        })
    return rows


def generate_vessels(count: int, customer_ids: list[int]) -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc)
    for i in range(count):
        prefix = random.choice(VESSEL_PREFIXES)
        suffix = random.choice(VESSEL_SUFFIXES)
        rows.append({
            "name": f"{prefix}{suffix}-{i:05d}",
            "imo_number": f"IMO{9000000 + i}",
            "customer_id": random.choice(customer_ids),
            "vessel_type": random.choice(VESSEL_TYPES),
            "created_at": now,
            "updated_at": now,
        })
    return rows


def generate_products(count: int) -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc)
    for i in range(count):
        prefix = random.choice(PRODUCT_PREFIXES)
        name = random.choice(PRODUCT_NAMES)
        category = random.choice(PRODUCT_CATEGORIES)
        rows.append({
            "name": f"{prefix}{name}-{i:05d}",
            "code": f"PRD{i:06d}",
            "specification": f"型号{random.choice('ABCDEF')}-{random.randint(100,999)}",
            "unit": random.choice(["件", "台", "个", "米", "桶", "套", "组"]),
            "brand": random.choice(BRANDS),
            "category": category,
            "created_at": now,
            "updated_at": now,
        })
    return rows


def generate_suppliers(count: int) -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc)
    for i in range(count):
        base_name = random.choice(SUPPLIER_NAMES)
        rows.append({
            "name": f"{base_name}-{i:04d}",
            "code": f"SUP{i:05d}",
            "type": random.choice([SupplierType.GOODS.value, SupplierType.SERVICE.value]),
            "contact_person": random_contact(),
            "contact_phone": random_phone(),
            "contact_email": f"supplier{i}@example.com",
            "address": f"中国某省某市工业区{i}号",
            "is_preferred": random.random() < 0.2,
            "created_at": now,
            "updated_at": now,
        })
    return rows


def generate_orders(
    count: int,
    customer_ids: list[int],
    vessel_ids: list[int],
    pm_id: int,
) -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc)
    statuses = [s.value for s in OrderStatus]
    project_types = [p.value for p in ProjectType]
    currencies = [c.value for c in Currency]

    for i in range(count):
        created = random_date_in_range(365, 0)
        rows.append({
            "order_no": f"ORD{created.strftime('%Y%m%d')}{i:06d}",
            "customer_id": random.choice(customer_ids),
            "vessel_id": random.choice(vessel_ids),
            "project_type": random.choice(project_types),
            "status": random.choice(statuses),
            "currency": random.choice(currencies),
            "total_amount": Decimal(str(random.randint(1000, 5000000))),
            "delivery_date": created + timedelta(days=random.randint(15, 120)),
            "pm_id": pm_id,
            "notes": random.choice(ORDER_NOTES_TEMPLATES).format(vessel="某船"),
            "created_at": now,
            "updated_at": now,
        })
    return rows


def generate_order_line_items(
    order_ids: list[int],
    product_ids: list[int],
    avg_items_per_order: int = 3,
) -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc)
    for order_id in order_ids:
        n_items = max(1, random.randint(avg_items_per_order - 1, avg_items_per_order + 2))
        for j in range(n_items):
            qty = Decimal(str(random.randint(1, 100)))
            price = Decimal(str(random.randint(50, 100000)))
            rows.append({
                "order_id": order_id,
                "product_id": random.choice(product_ids),
                "product_name": f"{random.choice(PRODUCT_PREFIXES)}{random.choice(PRODUCT_NAMES)}",
                "specification": f"型号{random.choice('ABCDEF')}-{random.randint(100,999)}",
                "unit": random.choice(["件", "台", "个", "米"]),
                "quantity": qty,
                "unit_price": price,
                "amount": qty * price,
                "created_at": now,
                "updated_at": now,
            })
    return rows


def generate_notifications(user_ids: list[int], count: int) -> list[dict]:
    rows = []
    now = datetime.now(timezone.utc)
    types = [t.value for t in NotificationType]
    titles = [
        "新订单待审批", "采购单已审批", "合同已签署", "发货提醒",
        "库存预警", "付款提醒", "工作流节点变更", "系统通知",
    ]
    for i in range(count):
        rows.append({
            "user_id": random.choice(user_ids),
            "type": random.choice(types),
            "title": random.choice(titles),
            "content": f"测试消息内容 #{i:07d}，请及时处理。",
            "is_read": random.random() < 0.5,
            "created_at": now,
            "updated_at": now,
        })
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
async def insert_batched(session: AsyncSession, table, rows: list[dict], label: str):
    """Insert rows in batches using Core INSERT for maximum speed."""
    total = len(rows)
    if total == 0:
        print(f"  {label}: 0 rows, skipped")
        return

    t0 = time.time()
    for start in range(0, total, BATCH_SIZE):
        batch = rows[start:start + BATCH_SIZE]
        await session.execute(insert(table), batch)
        pct = min(100, int((start + len(batch)) / total * 100))
        print(f"\r  {label}: {start + len(batch):,}/{total:,} ({pct}%)", end="", flush=True)
    elapsed = time.time() - t0
    rate = total / elapsed if elapsed > 0 else 0
    print(f"\r  {label}: {total:,} rows done in {elapsed:.1f}s ({rate:,.0f} rows/s)")


async def get_existing_ids(session: AsyncSession, model, limit=None):
    """Get all existing IDs from a table."""
    q = select(model.id)
    if limit:
        q = q.limit(limit)
    result = await session.execute(q)
    return [row[0] for row in result.fetchall()]


async def seed_bulk(
    n_orders: int = 10_000,
    n_products: int | None = None,
    n_customers: int | None = None,
):
    """Generate bulk test data."""
    # Auto-scale if not specified
    if n_customers is None:
        n_customers = max(20, n_orders // 50)
    if n_products is None:
        n_products = max(50, n_orders // 20)
    n_vessels = n_customers * 2
    n_suppliers = max(10, n_products // 10)
    n_line_items_approx = n_orders * 3
    n_notifications = min(n_orders, 100_000)

    print("=" * 60)
    print("LG Management — 批量数据生成")
    print("=" * 60)
    print(f"  订单 (orders):        {n_orders:>10,}")
    print(f"  客户 (customers):     {n_customers:>10,}")
    print(f"  船舶 (vessels):       {n_vessels:>10,}")
    print(f"  商品 (products):      {n_products:>10,}")
    print(f"  供应商 (suppliers):   {n_suppliers:>10,}")
    print(f"  行项目 (line_items):  ~{n_line_items_approx:>9,}")
    print(f"  通知 (notifications): {n_notifications:>10,}")
    total_approx = n_orders + n_customers + n_vessels + n_products + n_suppliers + n_line_items_approx + n_notifications
    print(f"  ────────────────────────────────")
    print(f"  总计约:               ~{total_approx:>9,} 行")
    print("=" * 60)

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
    )

    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_factory() as session:
        # Need at least one PM user
        pm_result = await session.execute(
            select(User.id).where(User.role == UserRole.PM).limit(1)
        )
        pm_id = pm_result.scalar()
        if pm_id is None:
            print("❌ 错误: 数据库中没有 PM 角色用户，请先运行 seed.py")
            return

        user_ids = await get_existing_ids(session, User)

        print("\n📦 生成数据中...\n")
        t_start = time.time()

        # 1. Customers
        customer_rows = generate_customers(n_customers)
        await insert_batched(session, Customer.__table__, customer_rows, "customers")
        await session.flush()
        customer_ids = await get_existing_ids(session, Customer)

        # 2. Vessels
        vessel_rows = generate_vessels(n_vessels, customer_ids)
        await insert_batched(session, Vessel.__table__, vessel_rows, "vessels")
        await session.flush()
        vessel_ids = await get_existing_ids(session, Vessel)

        # 3. Products
        product_rows = generate_products(n_products)
        await insert_batched(session, Product.__table__, product_rows, "products")
        await session.flush()
        product_ids = await get_existing_ids(session, Product)

        # 4. Suppliers
        supplier_rows = generate_suppliers(n_suppliers)
        await insert_batched(session, Supplier.__table__, supplier_rows, "suppliers")
        await session.flush()

        # 5. Orders
        order_rows = generate_orders(n_orders, customer_ids, vessel_ids, pm_id)
        await insert_batched(session, Order.__table__, order_rows, "orders")
        await session.flush()
        order_ids = await get_existing_ids(session, Order)

        # 6. Order Line Items (chunked to avoid OOM)
        print("  line_items: generating...")
        chunk_size = 10_000
        total_items = 0
        for chunk_start in range(0, len(order_ids), chunk_size):
            chunk_order_ids = order_ids[chunk_start:chunk_start + chunk_size]
            item_rows = generate_order_line_items(chunk_order_ids, product_ids)
            await insert_batched(
                session,
                OrderLineItem.__table__,
                item_rows,
                f"line_items (chunk {chunk_start // chunk_size + 1})",
            )
            total_items += len(item_rows)
            await session.flush()
        print(f"  line_items 总计: {total_items:,} rows")

        # 7. Notifications
        notif_rows = generate_notifications(user_ids, n_notifications)
        await insert_batched(session, Notification.__table__, notif_rows, "notifications")

        print("\n💾 提交事务...")
        await session.commit()

        elapsed = time.time() - t_start
        print(f"\n✅ 完成! 总用时 {elapsed:.1f}s")

        # Print table counts
        for model_cls in [Customer, Vessel, Product, Supplier, Order, OrderLineItem, Notification]:
            cnt = await session.scalar(select(func.count()).select_from(model_cls))
            print(f"  {model_cls.__tablename__}: {cnt:,}")

    await engine.dispose()


async def clean_bulk():
    """Remove bulk-generated data (keep first 10 rows per table as seed data)."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    print("🧹 清除压测数据...")
    # Tables to clean, in dependency order (children first)
    tables_to_clean = [
        "order_line_items",
        "notifications",
        "orders",
        "vessels",
        "customers",
        "products",
        "suppliers",
    ]

    async with async_session_factory() as session:
        for table in tables_to_clean:
            # Keep rows with id <= 10 (original seed data)
            result = await session.execute(
                text(f"DELETE FROM {table} WHERE id > 10")
            )
            print(f"  {table}: 删除 {result.rowcount:,} 行")
        await session.commit()

    await engine.dispose()
    print("✅ 清除完成")


def main():
    parser = argparse.ArgumentParser(description="LG Management 批量数据种子脚本")
    parser.add_argument("--orders", type=int, default=10_000, help="订单数量 (默认 10,000)")
    parser.add_argument("--products", type=int, default=None, help="商品数量 (默认按订单比例)")
    parser.add_argument("--customers", type=int, default=None, help="客户数量 (默认按订单比例)")
    parser.add_argument("--clean", action="store_true", help="清除压测数据")
    args = parser.parse_args()

    if args.clean:
        asyncio.run(clean_bulk())
    else:
        asyncio.run(seed_bulk(
            n_orders=args.orders,
            n_products=args.products,
            n_customers=args.customers,
        ))


if __name__ == "__main__":
    main()
