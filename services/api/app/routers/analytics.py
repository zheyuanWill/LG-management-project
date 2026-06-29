"""
Analytics Router — business intelligence endpoints.

All data comes from LG internal models (Settlement, Order, Procurement, etc.)
rather than Kingdee, giving real-time analytics independent of the accounting system.
"""
from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, extract, literal_column, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_user
from app.models.order import Order, OrderStatus, ProjectType, Currency
from app.models.contract import Contract, ContractStatus, PaymentRecord
from app.models.procurement import Procurement, ProcurementStatus, Disbursement
from app.models.settlement import Settlement, SettlementStatus, CostItem, CostCategory
from app.models.customer import Customer
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])

PROJECT_TYPE_LABELS = {
    "TECHNICAL_SERVICE": "技术服务",
    "SUPERVISION": "监管",
    "SPARE_PARTS": "备件供应",
    "IMPORT_EXPORT_AGENT": "进出口代理",
    "BROKERAGE": "经纪",
    "AGENCY_FEE": "代理费",
}


def _month_range(months: int):
    """Return (start_date, list_of_YYYYMM_keys)."""
    now = datetime.utcnow()
    start = (now - timedelta(days=months * 31)).replace(day=1)
    keys = []
    for i in range(months):
        dt = now - timedelta(days=(months - 1 - i) * 30)
        keys.append(f"{dt.year}-{dt.month:02d}")
    return start, keys


# ── 1. 月度盈利趋势 ────────────────────────────────────────────────

@router.get("/profitability")
async def get_profitability(
    months: int = Query(12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Monthly revenue / cost / profit / margin trend from approved settlements."""
    start, month_keys = _month_range(months)

    q = (
        select(
            extract("year", Settlement.approve_date).label("y"),
            extract("month", Settlement.approve_date).label("m"),
            func.coalesce(func.sum(Settlement.total_revenue_cny), 0).label("revenue"),
            func.coalesce(func.sum(Settlement.total_cost_cny), 0).label("cost"),
            func.coalesce(func.sum(Settlement.gross_profit), 0).label("profit"),
        )
        .where(
            Settlement.status.in_([SettlementStatus.APPROVED, SettlementStatus.COMPLETED]),
            Settlement.approve_date >= start.date(),
        )
        .group_by("y", "m")
    )
    rows = (await db.execute(q)).all()
    data_map = {}
    for r in rows:
        k = f"{int(r.y)}-{int(r.m):02d}"
        rev = float(r.revenue)
        cost = float(r.cost)
        profit = float(r.profit)
        margin = round(profit / rev * 100, 1) if rev else 0
        data_map[k] = {"revenue": rev, "cost": cost, "profit": profit, "margin": margin}

    result = []
    for k in month_keys:
        d = data_map.get(k, {"revenue": 0, "cost": 0, "profit": 0, "margin": 0})
        y, m = k.split("-")
        result.append({"month": k, "label": f"{m}月", **d})
    return result


# ── 2. 按客户营收 Top N ─────────────────────────────────────────────

@router.get("/revenue-by-customer")
async def revenue_by_customer(
    top: int = Query(10, ge=1, le=50),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        select(
            Customer.name.label("customer"),
            func.coalesce(func.sum(Settlement.total_revenue_cny), 0).label("revenue"),
            func.coalesce(func.sum(Settlement.gross_profit), 0).label("profit"),
            func.count().label("order_count"),
        )
        .join(Order, Settlement.order_id == Order.id)
        .join(Customer, Order.customer_id == Customer.id)
        .where(Settlement.status.in_([SettlementStatus.APPROVED, SettlementStatus.COMPLETED]))
    )
    if date_from:
        q = q.where(Settlement.approve_date >= date_from)
    if date_to:
        q = q.where(Settlement.approve_date <= date_to)

    q = q.group_by(Customer.id, Customer.name).order_by(desc("revenue")).limit(top)
    rows = (await db.execute(q)).all()
    return [
        {"customer": r.customer, "revenue": float(r.revenue), "profit": float(r.profit), "order_count": r.order_count}
        for r in rows
    ]


# ── 3. 按项目类型营收 ──────────────────────────────────────────────

@router.get("/revenue-by-project-type")
async def revenue_by_project_type(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        select(
            Order.project_type.label("type"),
            func.coalesce(func.sum(Settlement.total_revenue_cny), 0).label("revenue"),
            func.coalesce(func.sum(Settlement.gross_profit), 0).label("profit"),
            func.count().label("count"),
        )
        .join(Order, Settlement.order_id == Order.id)
        .where(Settlement.status.in_([SettlementStatus.APPROVED, SettlementStatus.COMPLETED]))
    )
    if date_from:
        q = q.where(Settlement.approve_date >= date_from)
    if date_to:
        q = q.where(Settlement.approve_date <= date_to)

    q = q.group_by(Order.project_type)
    rows = (await db.execute(q)).all()
    return [
        {
            "type": r.type,
            "label": PROJECT_TYPE_LABELS.get(r.type, r.type),
            "revenue": float(r.revenue),
            "profit": float(r.profit),
            "count": r.count,
        }
        for r in rows
    ]


# ── 4. 成本分类汇总 ───────────────────────────────────────────────

@router.get("/cost-breakdown")
async def cost_breakdown(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        select(
            CostCategory.name.label("category"),
            func.coalesce(func.sum(CostItem.amount_cny), 0).label("total"),
            func.count().label("count"),
        )
        .join(CostCategory, CostItem.category_id == CostCategory.id)
    )
    if date_from:
        q = q.where(CostItem.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        q = q.where(CostItem.created_at <= datetime.combine(date_to, datetime.max.time()))

    q = q.group_by(CostCategory.id, CostCategory.name).order_by(desc("total"))
    rows = (await db.execute(q)).all()
    return [{"category": r.category, "total": float(r.total), "count": r.count} for r in rows]


# ── 5. 现金流（收款 vs 付款）月度趋势 ────────────────────────────────

@router.get("/cashflow")
async def cashflow(
    months: int = Query(12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start, month_keys = _month_range(months)

    # Received payments
    recv_q = (
        select(
            extract("year", PaymentRecord.payment_date).label("y"),
            extract("month", PaymentRecord.payment_date).label("m"),
            func.coalesce(func.sum(PaymentRecord.amount_cny), 0).label("amount"),
        )
        .where(PaymentRecord.payment_date >= start.date())
        .group_by("y", "m")
    )
    recv_rows = (await db.execute(recv_q)).all()
    recv_map = {f"{int(r.y)}-{int(r.m):02d}": float(r.amount) for r in recv_rows}

    # Disbursed payments
    disb_q = (
        select(
            extract("year", Disbursement.payment_date).label("y"),
            extract("month", Disbursement.payment_date).label("m"),
            func.coalesce(func.sum(Disbursement.amount_cny), 0).label("amount"),
        )
        .where(Disbursement.payment_date >= start.date())
        .group_by("y", "m")
    )
    disb_rows = (await db.execute(disb_q)).all()
    disb_map = {f"{int(r.y)}-{int(r.m):02d}": float(r.amount) for r in disb_rows}

    result = []
    for k in month_keys:
        _, m = k.split("-")
        received = recv_map.get(k, 0)
        disbursed = disb_map.get(k, 0)
        result.append({
            "month": k,
            "label": f"{m}月",
            "received": received,
            "disbursed": disbursed,
            "net": round(received - disbursed, 2),
        })
    return result


# ── 6. 应收/应付余额 ─────────────────────────────────────────────

@router.get("/ar-ap")
async def ar_ap_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accounts receivable (contract amount - received) and accounts payable (procurement - disbursed)."""
    # AR: sum of effective contract amounts
    contract_total_q = select(
        func.coalesce(func.sum(Contract.total_amount), 0)
    ).where(Contract.status.notin_([ContractStatus.DRAFT, ContractStatus.TERMINATED]))
    contract_total = float((await db.execute(contract_total_q)).scalar() or 0)

    received_total_q = select(func.coalesce(func.sum(PaymentRecord.amount_cny), 0))
    received_total = float((await db.execute(received_total_q)).scalar() or 0)

    # AP: sum of approved procurement amounts
    procurement_total_q = select(
        func.coalesce(func.sum(Procurement.total_amount), 0)
    ).where(Procurement.status.notin_([ProcurementStatus.DRAFT, ProcurementStatus.CANCELLED]))
    procurement_total = float((await db.execute(procurement_total_q)).scalar() or 0)

    disbursed_total_q = select(func.coalesce(func.sum(Disbursement.amount_cny), 0))
    disbursed_total = float((await db.execute(disbursed_total_q)).scalar() or 0)

    ar = round(contract_total - received_total, 2)
    ap = round(procurement_total - disbursed_total, 2)

    return {
        "accounts_receivable": ar,
        "accounts_payable": ap,
        "contract_total": contract_total,
        "received_total": received_total,
        "procurement_total": procurement_total,
        "disbursed_total": disbursed_total,
        "net_position": round(ar - ap, 2),
    }


# ── 7. 项目利润分析表 ────────────────────────────────────────────

@router.get("/project-profitability")
async def project_profitability(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    customer_id: Optional[int] = None,
    project_type: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = Query("revenue", pattern="^(revenue|cost|profit|margin|received_rate)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-order profitability with nested cost breakdown."""
    q = (
        select(Order)
        .options(selectinload(Order.customer))
    )
    if customer_id:
        q = q.where(Order.customer_id == customer_id)
    if project_type:
        q = q.where(Order.project_type == project_type)
    if status:
        q = q.where(Order.status == status)

    q = q.where(Order.status != OrderStatus.CANCELLED)
    orders = (await db.execute(q)).scalars().all()

    if not orders:
        return {"rows": [], "summary": {}}

    order_ids = [o.id for o in orders]

    # Settlements grouped by order
    stl_q = (
        select(
            Settlement.order_id,
            func.coalesce(func.sum(Settlement.total_revenue_cny), 0).label("revenue"),
            func.coalesce(func.sum(Settlement.total_cost_cny), 0).label("cost"),
            func.coalesce(func.sum(Settlement.gross_profit), 0).label("profit"),
        )
        .where(
            Settlement.order_id.in_(order_ids),
            Settlement.status.in_([SettlementStatus.APPROVED, SettlementStatus.COMPLETED]),
        )
        .group_by(Settlement.order_id)
    )
    stl_rows = (await db.execute(stl_q)).all()
    stl_map = {r.order_id: r for r in stl_rows}

    # Payment received per order
    recv_q = (
        select(
            PaymentRecord.order_id,
            func.coalesce(func.sum(PaymentRecord.amount_cny), 0).label("received"),
        )
        .where(PaymentRecord.order_id.in_(order_ids))
        .group_by(PaymentRecord.order_id)
    )
    recv_rows = (await db.execute(recv_q)).all()
    recv_map = {r.order_id: float(r.received) for r in recv_rows}

    # Disbursed per order
    disb_q = (
        select(
            Disbursement.order_id,
            func.coalesce(func.sum(Disbursement.amount_cny), 0).label("disbursed"),
        )
        .where(Disbursement.order_id.in_(order_ids))
        .group_by(Disbursement.order_id)
    )
    disb_rows = (await db.execute(disb_q)).all()
    disb_map = {r.order_id: float(r.disbursed) for r in disb_rows}

    # Cost items per order
    cost_q = (
        select(CostItem)
        .options(selectinload(CostItem.category))
        .where(CostItem.order_id.in_(order_ids))
    )
    cost_items = (await db.execute(cost_q)).scalars().all()
    cost_map: dict[int, list] = {}
    for ci in cost_items:
        cost_map.setdefault(ci.order_id, []).append({
            "category": ci.category.name if ci.category else "未分类",
            "description": ci.description,
            "amount_cny": float(ci.amount_cny),
            "invoice_no": ci.invoice_no,
        })

    rows = []
    total_rev = total_cost = total_profit = total_recv = total_disb = 0

    for o in orders:
        stl = stl_map.get(o.id)
        rev = float(stl.revenue) if stl else 0
        cost = float(stl.cost) if stl else 0
        profit = float(stl.profit) if stl else 0
        margin = round(profit / rev * 100, 1) if rev else 0
        received = recv_map.get(o.id, 0)
        disbursed = disb_map.get(o.id, 0)
        received_rate = round(received / rev * 100, 1) if rev else 0

        if date_from and o.created_at and o.created_at.date() < date_from:
            continue
        if date_to and o.created_at and o.created_at.date() > date_to:
            continue

        total_rev += rev
        total_cost += cost
        total_profit += profit
        total_recv += received
        total_disb += disbursed

        rows.append({
            "order_id": o.id,
            "order_no": o.order_no,
            "customer": o.customer.name if o.customer else "—",
            "project_type": PROJECT_TYPE_LABELS.get(o.project_type, o.project_type),
            "status": o.status,
            "revenue": rev,
            "cost": cost,
            "profit": profit,
            "margin": margin,
            "received": received,
            "received_rate": received_rate,
            "disbursed": disbursed,
            "cost_items": cost_map.get(o.id, []),
        })

    sort_key = sort_by if sort_by != "margin" else "margin"
    rows.sort(key=lambda x: x.get(sort_key, 0), reverse=(sort_order == "desc"))

    return {
        "rows": rows,
        "summary": {
            "total_revenue": round(total_rev, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "total_margin": round(total_profit / total_rev * 100, 1) if total_rev else 0,
            "total_received": round(total_recv, 2),
            "total_disbursed": round(total_disb, 2),
            "order_count": len(rows),
        },
    }


# ── 8. 同步日志查询 ─────────────────────────────────────────────

@router.get("/sync-logs")
async def get_sync_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    entity_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.sync_log import SyncLog, SyncStatus

    q = select(SyncLog).order_by(SyncLog.created_at.desc())
    count_q = select(func.count()).select_from(SyncLog)

    if status:
        q = q.where(SyncLog.status == status)
        count_q = count_q.where(SyncLog.status == status)
    if entity_type:
        q = q.where(SyncLog.entity_type == entity_type)
        count_q = count_q.where(SyncLog.entity_type == entity_type)

    total = (await db.execute(count_q)).scalar() or 0
    logs = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    # Summary counts
    summary_q = select(
        SyncLog.status, func.count().label("cnt")
    ).group_by(SyncLog.status)
    summary_rows = (await db.execute(summary_q)).all()
    summary = {r.status: r.cnt for r in summary_rows}

    return {
        "items": [
            {
                "id": l.id,
                "entity_type": l.entity_type,
                "entity_id": l.entity_id,
                "kingdee_doc_type": l.kingdee_doc_type,
                "kingdee_doc_no": l.kingdee_doc_no,
                "direction": l.direction,
                "status": l.status,
                "error_message": l.error_message,
                "retry_count": l.retry_count,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ],
        "total": total,
        "summary": summary,
    }
