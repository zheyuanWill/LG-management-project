"""Seed script to generate 30+ historical orders (projects) for AI features demo."""
import asyncio
import random
from decimal import Decimal
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.config import settings
from app.db.base import Base
from app.models.user import User, UserRole
from app.models.customer import Customer, Vessel
from app.models.product import Product, Supplier
from app.models.order import (
    Order, OrderLineItem, Quote, QuoteLineItem,
    ProjectType, OrderStatus, QuoteStatus, Currency,
)
from app.models.contract import Contract, PaymentPlan, ContractStatus
from app.models.tracking import NodeTemplate, TrackingNode, NodeStatus

SHIP_NAMES = [
    "远洋号", "海运之星", "招商远航", "长江壹号", "南海翡翠",
    "渤海明珠", "黄海之光", "太平洋号", "东方明珠", "北斗星辰",
    "地中海号", "大西洋号", "印度洋号", "珠江水手", "东海龙王",
]

PROJECT_DESCS = {
    ProjectType.SPARE_PARTS: [
        "主机缸套及活塞环更换", "液压泵组维修备件", "阀门批量采购",
        "电缆更新换装", "甲板机械备件", "舵机液压系统备件",
        "锅炉配件采购", "空压机维修配件", "发电机组备件供应",
        "分油机备件", "海水泵维修件", "燃油系统配件",
    ],
    ProjectType.TECHNICAL_SERVICE: [
        "主机大修技术服务", "轮机维护保养", "甲板机械检修",
        "电气系统检测", "船体钢结构修复", "涂装工程服务",
        "舵机检修服务", "锅炉清洗检验", "管路系统改造",
    ],
    ProjectType.SUPERVISION: [
        "坞修监工服务", "航修监督检验", "新造船监理",
        "设备安装监工", "海试监督",
    ],
}


def _rand_amount(low: int, high: int) -> Decimal:
    return Decimal(str(random.randint(low, high))).quantize(Decimal("0.01"))


def _rand_date_past(max_days: int = 365) -> date:
    return date.today() - timedelta(days=random.randint(1, max_days))


async def seed_historical():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        existing = await db.execute(
            select(Order).where(Order.notes.like("%历史%")).limit(1)
        )
        if existing.scalar_one_or_none():
            print("Historical orders already exist. Skipping...")
            return

        users = (await db.execute(select(User))).scalars().all()
        customers = (await db.execute(select(Customer))).scalars().all()
        vessels = (await db.execute(select(Vessel))).scalars().all()
        products = (await db.execute(select(Product))).scalars().all()
        suppliers = (await db.execute(select(Supplier))).scalars().all()
        node_templates_spare = (await db.execute(
            select(NodeTemplate).where(
                NodeTemplate.project_type == ProjectType.SPARE_PARTS
            ).order_by(NodeTemplate.sort_order)
        )).scalars().all()
        node_templates_tech = (await db.execute(
            select(NodeTemplate).where(
                NodeTemplate.project_type == ProjectType.TECHNICAL_SERVICE
            ).order_by(NodeTemplate.sort_order)
        )).scalars().all()

        if not users or not customers:
            print("No base data. Run seed.py first.")
            return

        pm_users = [u for u in users if u.role in (UserRole.PM, UserRole.OWNER)]
        if not pm_users:
            pm_users = users[:1]

        order_count = 0
        project_types_to_gen = [
            (ProjectType.SPARE_PARTS, 14),
            (ProjectType.TECHNICAL_SERVICE, 10),
            (ProjectType.SUPERVISION, 6),
            (ProjectType.IMPORT_EXPORT_AGENT, 3),
        ]

        for pt, n_orders in project_types_to_gen:
            descs = PROJECT_DESCS.get(pt, [f"{pt.value}项目"])
            templates = (node_templates_spare if pt == ProjectType.SPARE_PARTS
                         else node_templates_tech if pt == ProjectType.TECHNICAL_SERVICE
                         else [])

            for i in range(n_orders):
                cust = random.choice(customers)
                cust_vessels = [v for v in vessels if v.customer_id == cust.id]
                vessel = random.choice(cust_vessels) if cust_vessels else (
                    random.choice(vessels) if vessels else None)
                ship_name = vessel.name if vessel else random.choice(SHIP_NAMES)

                desc = random.choice(descs)
                order_date = _rand_date_past(360)
                status = random.choice(
                    [OrderStatus.COMPLETED] * 6
                    + [OrderStatus.IN_PROGRESS] * 3
                    + [OrderStatus.CANCELLED]
                )
                currency = random.choice([Currency.CNY] * 7 + [Currency.USD] * 3)

                base_amount = _rand_amount(20000, 500000)

                order = Order(
                    order_no=f"ORD{order_date.strftime('%Y%m%d')}{order_count + 100:03d}",
                    customer_id=cust.id,
                    vessel_id=vessel.id if vessel else None,
                    project_type=pt,
                    status=status,
                    currency=currency,
                    total_amount=base_amount,
                    delivery_date=order_date + timedelta(days=random.randint(15, 90)),
                    pm_id=random.choice(pm_users).id,
                    notes=f"[历史] {ship_name} - {desc}",
                )
                db.add(order)
                await db.flush()

                n_items = random.randint(1, 5)
                line_total = Decimal("0")
                for li in range(n_items):
                    prod = random.choice(products) if products else None
                    qty = Decimal(str(random.randint(1, 20)))
                    price = _rand_amount(500, 80000)
                    amt = (qty * price).quantize(Decimal("0.01"))
                    line_total += amt

                    item = OrderLineItem(
                        order_id=order.id,
                        product_id=prod.id if prod else None,
                        product_name=prod.name if prod else f"物料-{li+1}",
                        specification=prod.specification if prod else "",
                        unit=prod.unit if prod else "件",
                        quantity=qty,
                        unit_price=price,
                        amount=amt,
                    )
                    db.add(item)

                order.total_amount = line_total
                await db.flush()

                if status in (OrderStatus.COMPLETED, OrderStatus.IN_PROGRESS):
                    quote = Quote(
                        quote_no=f"QT-{order.order_no}-V01",
                        order_id=order.id,
                        version=1,
                        status=QuoteStatus.ACCEPTED,
                        currency=currency,
                        total_amount=line_total,
                        valid_until=order_date + timedelta(days=30),
                        notes="报价已确认",
                    )
                    db.add(quote)
                    await db.flush()

                    contract = Contract(
                        contract_no=f"CON{order.order_no[3:]}",
                        order_id=order.id,
                        quote_id=quote.id,
                        customer_id=cust.id,
                        title=f"{ship_name} - {desc}",
                        status=(ContractStatus.COMPLETED
                                if status == OrderStatus.COMPLETED
                                else ContractStatus.EXECUTING),
                        currency=currency,
                        total_amount=line_total,
                        signed_date=order_date + timedelta(days=random.randint(3, 10)),
                        effective_date=order_date + timedelta(days=random.randint(3, 10)),
                        expiry_date=order_date + timedelta(days=random.randint(60, 180)),
                        payment_terms="预付30%，发货前付40%，验收后付30%",
                    )
                    db.add(contract)
                    await db.flush()

                    phases = [("预付款", 30), ("中期款", 40), ("尾款", 30)]
                    for phase_name, pct in phases:
                        planned_amt = (line_total * Decimal(str(pct)) / 100).quantize(Decimal("0.01"))
                        plan = PaymentPlan(
                            contract_id=contract.id,
                            phase=phase_name,
                            percentage=Decimal(str(pct)),
                            planned_amount=planned_amt,
                            planned_date=order_date + timedelta(days=random.randint(5, 60)),
                        )
                        if status == OrderStatus.COMPLETED:
                            plan.actual_amount = planned_amt
                            plan.actual_date = plan.planned_date + timedelta(
                                days=random.randint(-3, 5))
                        db.add(plan)

                if templates:
                    for tmpl in templates:
                        node_date = order_date + timedelta(days=tmpl.sort_order * 3)
                        if status == OrderStatus.COMPLETED:
                            ns = NodeStatus.COMPLETED
                        elif status == OrderStatus.IN_PROGRESS:
                            if tmpl.sort_order <= 4:
                                ns = NodeStatus.COMPLETED
                            elif tmpl.sort_order == 5:
                                ns = NodeStatus.IN_PROGRESS
                            else:
                                ns = NodeStatus.PENDING
                        else:
                            ns = NodeStatus.PENDING

                        node = TrackingNode(
                            order_id=order.id,
                            template_id=tmpl.id,
                            name=tmpl.name,
                            status=ns,
                            planned_date=node_date,
                            actual_date=node_date if ns == NodeStatus.COMPLETED else None,
                            sort_order=tmpl.sort_order,
                        )
                        db.add(node)

                order_count += 1

        await db.commit()
        print(f"Seeded {order_count} historical orders successfully!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_historical())
