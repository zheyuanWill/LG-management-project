"""Agent Tools — 4 tools for project management queries."""
import json
from decimal import Decimal
from typing import Optional

from sqlalchemy import create_engine, select, or_, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.order import Order, OrderLineItem, OrderStatus, ProjectType, Currency
from app.models.customer import Customer, Vessel
from app.models.contract import Contract, PaymentPlan, ContractStatus
from app.models.procurement import Procurement, ProcurementLineItem
from app.models.tracking import TrackingNode, NodeStatus
from app.models.user import User

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
        _engine = create_engine(sync_url)
    return _engine


def _decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


def search_orders(keyword: str, limit: int = 10) -> str:
    """搜索订单/项目。支持按订单号、客户名、船名、备注模糊搜索。

    Args:
        keyword: 搜索关键词
        limit: 最大返回条数，默认10
    """
    engine = _get_engine()
    with Session(engine) as db:
        query = (
            select(
                Order.id, Order.order_no, Order.status, Order.project_type,
                Order.currency, Order.total_amount, Order.delivery_date, Order.notes,
                Customer.name.label("customer_name"),
                Vessel.name.label("vessel_name"),
            )
            .join(Customer, Order.customer_id == Customer.id)
            .outerjoin(Vessel, Order.vessel_id == Vessel.id)
            .where(
                or_(
                    Order.order_no.ilike(f"%{keyword}%"),
                    Order.notes.ilike(f"%{keyword}%"),
                    Customer.name.ilike(f"%{keyword}%"),
                    Vessel.name.ilike(f"%{keyword}%"),
                )
            )
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        rows = db.execute(query).all()

        results = []
        for r in rows:
            results.append({
                "order_id": r.id,
                "order_no": r.order_no,
                "customer": r.customer_name,
                "vessel": r.vessel_name,
                "status": r.status.value if r.status else "",
                "project_type": r.project_type.value if r.project_type else "",
                "total_amount": float(r.total_amount or 0),
                "currency": r.currency.value if r.currency else "CNY",
                "delivery_date": str(r.delivery_date) if r.delivery_date else "",
                "notes": r.notes or "",
            })

        return json.dumps({"count": len(results), "orders": results}, ensure_ascii=False, default=_decimal_default)


def get_project_detail(order_id: int) -> str:
    """获取订单/项目的完整详情，包括合同、采购单、跟踪节点。

    Args:
        order_id: 订单ID
    """
    engine = _get_engine()
    with Session(engine) as db:
        order = db.get(Order, order_id)
        if not order:
            return json.dumps({"error": f"订单 {order_id} 不存在"}, ensure_ascii=False)

        customer = db.get(Customer, order.customer_id)
        vessel = db.get(Vessel, order.vessel_id) if order.vessel_id else None
        pm = db.get(User, order.pm_id) if order.pm_id else None

        line_items = db.execute(
            select(OrderLineItem).where(OrderLineItem.order_id == order_id)
        ).scalars().all()

        contracts = db.execute(
            select(Contract).where(Contract.order_id == order_id)
        ).scalars().all()

        procurements = db.execute(
            select(Procurement).where(Procurement.order_id == order_id)
        ).scalars().all()

        nodes = db.execute(
            select(TrackingNode).where(TrackingNode.order_id == order_id)
            .order_by(TrackingNode.sort_order)
        ).scalars().all()

        detail = {
            "order": {
                "id": order.id,
                "order_no": order.order_no,
                "status": order.status.value,
                "project_type": order.project_type.value,
                "total_amount": float(order.total_amount or 0),
                "currency": order.currency.value,
                "delivery_date": str(order.delivery_date) if order.delivery_date else "",
                "notes": order.notes or "",
                "customer": customer.name if customer else "",
                "vessel": vessel.name if vessel else "",
                "pm": pm.real_name if pm else "",
            },
            "line_items": [
                {
                    "product": li.product_name,
                    "spec": li.specification or "",
                    "qty": float(li.quantity),
                    "unit_price": float(li.unit_price),
                    "amount": float(li.amount),
                }
                for li in line_items
            ],
            "contracts": [
                {
                    "contract_no": c.contract_no,
                    "title": c.title,
                    "status": c.status.value,
                    "total_amount": float(c.total_amount or 0),
                    "signed_date": str(c.signed_date) if c.signed_date else "",
                }
                for c in contracts
            ],
            "procurements": [
                {
                    "procurement_no": p.procurement_no,
                    "status": p.status.value,
                    "total_amount": float(p.total_amount or 0),
                    "expected_date": str(p.expected_date) if p.expected_date else "",
                }
                for p in procurements
            ],
            "tracking": [
                {
                    "name": n.name,
                    "status": n.status.value,
                    "planned_date": str(n.planned_date) if n.planned_date else "",
                    "actual_date": str(n.actual_date) if n.actual_date else "",
                }
                for n in nodes
            ],
        }
        return json.dumps(detail, ensure_ascii=False, default=_decimal_default)


def calculate_cost(order_id: int) -> str:
    """计算项目成本，对比预算与实际支出。

    Args:
        order_id: 订单ID
    """
    engine = _get_engine()
    with Session(engine) as db:
        order = db.get(Order, order_id)
        if not order:
            return json.dumps({"error": f"订单 {order_id} 不存在"}, ensure_ascii=False)

        budget = float(order.total_amount or 0)

        proc_total = db.execute(
            select(func.sum(Procurement.total_amount)).where(Procurement.order_id == order_id)
        ).scalar() or Decimal("0")

        contracts = db.execute(
            select(Contract).where(Contract.order_id == order_id)
        ).scalars().all()

        paid = Decimal("0")
        planned_payments = Decimal("0")
        for c in contracts:
            plans = db.execute(
                select(PaymentPlan).where(PaymentPlan.contract_id == c.id)
            ).scalars().all()
            for p in plans:
                planned_payments += p.planned_amount or Decimal("0")
                if p.actual_amount:
                    paid += p.actual_amount

        result = {
            "order_no": order.order_no,
            "currency": order.currency.value,
            "budget": float(budget),
            "procurement_cost": float(proc_total),
            "planned_payments": float(planned_payments),
            "actual_paid": float(paid),
            "remaining_budget": float(Decimal(str(budget)) - proc_total),
            "budget_usage_pct": round(float(proc_total) / budget * 100, 1) if budget > 0 else 0,
            "payment_progress_pct": round(float(paid) / float(planned_payments) * 100, 1) if planned_payments > 0 else 0,
        }
        return json.dumps(result, ensure_ascii=False, default=_decimal_default)


def generate_report(order_id: int) -> str:
    """将项目的结构化数据生成可读的文字报告摘要。

    Args:
        order_id: 订单ID
    """
    detail_json = get_project_detail(order_id)
    detail = json.loads(detail_json)
    if "error" in detail:
        return detail_json

    o = detail["order"]
    lines = [
        f"# {o['order_no']} 项目报告",
        f"**客户**: {o['customer']}  **船舶**: {o['vessel']}  **项目经理**: {o['pm']}",
        f"**类型**: {o['project_type']}  **状态**: {o['status']}",
        f"**合同金额**: {o['currency']} {o['total_amount']:,.2f}",
        f"**交付日期**: {o['delivery_date']}",
        "",
        "## 物料清单",
    ]
    for li in detail["line_items"]:
        lines.append(f"- {li['product']} ({li['spec']}) × {li['qty']} = {li['amount']:,.2f}")

    if detail["contracts"]:
        lines.append("\n## 合同")
        for c in detail["contracts"]:
            lines.append(f"- {c['contract_no']}: {c['title']} — {c['status']} ({c['total_amount']:,.2f})")

    if detail["tracking"]:
        lines.append("\n## 进度跟踪")
        for n in detail["tracking"]:
            status_emoji = {"COMPLETED": "✅", "IN_PROGRESS": "🔄", "PENDING": "⏳", "OVERDUE": "⚠️"}.get(n["status"], "❓")
            lines.append(f"- {status_emoji} {n['name']}: {n['status']} (计划: {n['planned_date']})")

    cost_json = calculate_cost(order_id)
    cost = json.loads(cost_json)
    if "error" not in cost:
        lines.append(f"\n## 成本概况")
        lines.append(f"- 预算: {cost['budget']:,.2f}")
        lines.append(f"- 采购成本: {cost['procurement_cost']:,.2f} ({cost['budget_usage_pct']}%)")
        lines.append(f"- 已付款: {cost['actual_paid']:,.2f}")
        lines.append(f"- 剩余预算: {cost['remaining_budget']:,.2f}")

    return "\n".join(lines)


def search_knowledge(query: str, limit: int = 5) -> str:
    """在知识库中搜索相关文档，包括紧急预案、项目经验、ISO文件、法规标准等。

    Args:
        query: 搜索关键词或问题
        limit: 最大返回条数，默认5
    """
    from app.models.iso_process import KnowledgeDocument
    engine = _get_engine()
    with Session(engine) as db:
        results = db.execute(
            select(KnowledgeDocument)
            .where(
                or_(
                    KnowledgeDocument.title.ilike(f"%{query}%"),
                    KnowledgeDocument.content.ilike(f"%{query}%"),
                )
            )
            .order_by(KnowledgeDocument.created_at.desc())
            .limit(limit)
        ).scalars().all()

        docs = []
        for doc in results:
            docs.append({
                "id": doc.id,
                "title": doc.title,
                "doc_type": doc.doc_type,
                "content": (doc.content or "")[:500],
                "source_type": doc.source_type,
            })
        return json.dumps({"count": len(docs), "documents": docs}, ensure_ascii=False)


def search_web(query: str) -> str:
    """在网络上搜索实时信息，如行业规范、法规、标准、供应商信息等。

    Args:
        query: 搜索查询
    """
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            formatted = []
            for r in results:
                formatted.append({
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "href": r.get("href", ""),
                })
            return json.dumps({"count": len(formatted), "results": formatted}, ensure_ascii=False)
    except ImportError:
        return json.dumps({"error": "Web search not available (duckduckgo-search not installed)"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"}, ensure_ascii=False)


def analyze_supplier(supplier_id: int) -> str:
    """综合分析供应商表现，包括历史合作、评分、准入状态等。

    Args:
        supplier_id: 供应商ID
    """
    from app.models.product import Supplier
    from app.models.iso_process import SupplierEvaluation, SupplierAdmission
    engine = _get_engine()
    with Session(engine) as db:
        supplier = db.get(Supplier, supplier_id)
        if not supplier:
            return json.dumps({"error": f"供应商 {supplier_id} 不存在"}, ensure_ascii=False)

        evaluations = db.execute(
            select(SupplierEvaluation)
            .where(SupplierEvaluation.supplier_id == supplier_id)
            .order_by(SupplierEvaluation.year.desc())
            .limit(3)
        ).scalars().all()

        proc_count = db.execute(
            select(func.count()).select_from(Procurement)
            .where(Procurement.supplier_id == supplier_id)
        ).scalar() or 0

        result = {
            "supplier": {
                "id": supplier.id,
                "name": supplier.name,
                "code": supplier.code,
                "type": supplier.type.value if supplier.type else "",
                "qualification_status": supplier.qualification_status or "QUALIFIED",
                "evaluation_score": float(supplier.evaluation_score) if supplier.evaluation_score else None,
                "evaluation_level": supplier.evaluation_level,
                "is_preferred": supplier.is_preferred,
            },
            "procurement_count": proc_count,
            "recent_evaluations": [
                {
                    "year": e.year,
                    "total_score": float(e.total_score) if e.total_score else None,
                    "level": e.level.value if e.level else None,
                    "quality": float(e.quality_score) if e.quality_score else None,
                    "delivery": float(e.delivery_score) if e.delivery_score else None,
                    "price": float(e.price_score) if e.price_score else None,
                    "service": float(e.service_score) if e.service_score else None,
                }
                for e in evaluations
            ],
        }
        return json.dumps(result, ensure_ascii=False, default=_decimal_default)


TOOL_DEFINITIONS = [
    {
        "name": "search_orders",
        "func": search_orders,
        "description": "搜索订单/项目。支持按订单号、客户名、船名、备注模糊搜索。",
    },
    {
        "name": "get_project_detail",
        "func": get_project_detail,
        "description": "获取订单/项目的完整详情，包括合同、采购单、跟踪节点。",
    },
    {
        "name": "calculate_cost",
        "func": calculate_cost,
        "description": "计算项目成本，对比预算与实际支出。",
    },
    {
        "name": "generate_report",
        "func": generate_report,
        "description": "将项目的结构化数据生成可读的 Markdown 格式报告摘要。",
    },
    {
        "name": "search_knowledge",
        "func": search_knowledge,
        "description": "在知识库中搜索相关文档，包括紧急预案、项目经验、ISO文件、法规标准、投诉处理经验等。",
    },
    {
        "name": "search_web",
        "func": search_web,
        "description": "在网络上搜索实时信息，如行业规范、法规、标准、市场信息等。需要参考外部资料时使用。",
    },
    {
        "name": "analyze_supplier",
        "func": analyze_supplier,
        "description": "综合分析供应商表现，包括历史合作、评分、准入状态、近年评价趋势等。",
    },
]
