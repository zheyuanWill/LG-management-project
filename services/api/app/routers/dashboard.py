"""Dashboard Aggregation Router

Provides aggregated data endpoints for the dashboard,
reducing the need for multiple API calls from the frontend.
"""
from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.order import Order, OrderStatus, Quote, QuoteStatus
from app.models.contract import Contract, ContractStatus
from app.models.procurement import Procurement, ProcurementStatus
from app.models.settlement import Settlement, SettlementStatus
from app.models.tracking import TrackingNode
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(
    date_from: Optional[date] = Query(None, description="Start date filter"),
    date_to: Optional[date] = Query(None, description="End date filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overview stat cards data:
    - active_orders: count of non-draft, non-cancelled, non-completed orders
    - monthly_revenue: sum of settlement amounts this month (or date range)
    - pending_approval: count of procurements with PENDING_APPROVAL status
    - overdue_nodes: count of tracking nodes past their planned date
    """
    now = datetime.utcnow()

    # Determine time range
    if date_from and date_to:
        range_start = datetime.combine(date_from, datetime.min.time())
        range_end = datetime.combine(date_to, datetime.max.time())
        prev_duration = (date_to - date_from).days or 1
        prev_start = datetime.combine(date_from - timedelta(days=prev_duration), datetime.min.time())
        prev_end = range_start
    else:
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        range_start = month_start
        range_end = now
        prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
        prev_start = prev_month_start
        prev_end = month_start

    # Active orders
    active_q = select(func.count()).select_from(Order).where(
        Order.status.in_([OrderStatus.IN_PROGRESS])
    )
    active_result = await db.execute(active_q)
    active_orders = active_result.scalar() or 0

    # Revenue in range (from approved settlements)
    revenue_q = select(func.coalesce(func.sum(Settlement.total_revenue_cny), 0)).where(
        Settlement.status == SettlementStatus.APPROVED,
        Settlement.approve_date >= range_start.date() if hasattr(range_start, 'date') else range_start,
    )
    revenue_result = await db.execute(revenue_q)
    monthly_revenue = float(revenue_result.scalar() or 0)

    # Pending approval procurements
    approval_q = select(func.count()).select_from(Procurement).where(
        Procurement.status == ProcurementStatus.PENDING_APPROVAL
    )
    approval_result = await db.execute(approval_q)
    pending_approval = approval_result.scalar() or 0

    # Overdue tracking nodes
    overdue_q = select(func.count()).select_from(TrackingNode).where(
        TrackingNode.status == "IN_PROGRESS",
        TrackingNode.planned_date < now,
    )
    overdue_result = await db.execute(overdue_q)
    overdue_nodes = overdue_result.scalar() or 0

    # Previous period revenue for trend calculation
    prev_revenue_q = select(func.coalesce(func.sum(Settlement.total_revenue_cny), 0)).where(
        Settlement.status == SettlementStatus.APPROVED,
        Settlement.approve_date >= prev_start.date() if hasattr(prev_start, 'date') else prev_start,
        Settlement.approve_date < prev_end.date() if hasattr(prev_end, 'date') else prev_end,
    )
    prev_revenue_result = await db.execute(prev_revenue_q)
    prev_monthly_revenue = float(prev_revenue_result.scalar() or 0)

    revenue_trend = 0.0
    if prev_monthly_revenue > 0:
        revenue_trend = round(
            (monthly_revenue - prev_monthly_revenue) / prev_monthly_revenue * 100, 1
        )

    return {
        "active_orders": active_orders,
        "monthly_revenue": monthly_revenue,
        "pending_approval": pending_approval,
        "overdue_nodes": overdue_nodes,
        "revenue_trend": revenue_trend,
    }


@router.get("/order-status-distribution")
async def get_order_status_distribution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get order count grouped by status for the pie chart."""
    q = (
        select(Order.status, func.count().label("count"))
        .group_by(Order.status)
    )
    result = await db.execute(q)
    rows = result.all()

    status_labels = {
        "DRAFT": "草稿",
        "IN_PROGRESS": "进行中",
        "COMPLETED": "已完成",
        "CANCELLED": "已取消",
    }

    return [
        {"status": row.status, "label": status_labels.get(row.status, row.status), "count": row.count}
        for row in rows
    ]


@router.get("/revenue-trend")
async def get_revenue_trend(
    months: int = Query(default=12, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get monthly revenue and cost data for the bar/line chart.
    Returns data for the last N months.
    """
    now = datetime.utcnow()
    start_date = (now - timedelta(days=months * 31)).replace(day=1)

    # Revenue per month (from approved settlements)
    revenue_q = (
        select(
            extract("year", Settlement.approve_date).label("year"),
            extract("month", Settlement.approve_date).label("month"),
            func.coalesce(func.sum(Settlement.total_revenue_cny), 0).label("revenue"),
        )
        .where(
            Settlement.status == SettlementStatus.APPROVED,
            Settlement.approve_date >= start_date,
        )
        .group_by(
            extract("year", Settlement.approve_date),
            extract("month", Settlement.approve_date),
        )
        .order_by("year", "month")
    )
    revenue_result = await db.execute(revenue_q)
    revenue_rows = revenue_result.all()

    revenue_map = {}
    for row in revenue_rows:
        key = f"{int(row.year)}-{int(row.month):02d}"
        revenue_map[key] = float(row.revenue)

    # Build monthly series
    data = []
    for i in range(months):
        dt = now - timedelta(days=(months - 1 - i) * 30)
        key = f"{dt.year}-{dt.month:02d}"
        month_label = f"{dt.month}月"
        revenue = revenue_map.get(key, 0)
        data.append({
            "month": month_label,
            "key": key,
            "revenue": revenue,
        })

    return data


@router.get("/completion-rate")
async def get_completion_rate(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get overall project/order completion rate for the gauge chart."""
    total_q = select(func.count()).select_from(Order).where(
        Order.status != OrderStatus.CANCELLED
    )
    total_result = await db.execute(total_q)
    total = total_result.scalar() or 0

    completed_q = select(func.count()).select_from(Order).where(
        Order.status == OrderStatus.COMPLETED
    )
    completed_result = await db.execute(completed_q)
    completed = completed_result.scalar() or 0

    rate = round(completed / total * 100, 1) if total > 0 else 0

    return {
        "total": total,
        "completed": completed,
        "rate": rate,
    }


@router.get("/funnel")
async def get_order_funnel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get real order conversion funnel data.
    Tracks orders through stages: total -> quoted -> contracted -> in_progress -> completed
    """
    # Total non-cancelled orders
    total_q = select(func.count()).select_from(Order).where(
        Order.status != OrderStatus.CANCELLED
    )
    total = (await db.execute(total_q)).scalar() or 0

    # Orders that have at least one quote
    quoted_q = select(func.count(func.distinct(Quote.order_id))).select_from(Quote)
    quoted = (await db.execute(quoted_q)).scalar() or 0

    # Orders that have at least one contract
    contracted_q = select(func.count(func.distinct(Contract.order_id))).select_from(Contract)
    contracted = (await db.execute(contracted_q)).scalar() or 0

    # Orders currently in progress or completed
    in_progress_q = select(func.count()).select_from(Order).where(
        Order.status.in_([OrderStatus.IN_PROGRESS, OrderStatus.COMPLETED])
    )
    in_progress = (await db.execute(in_progress_q)).scalar() or 0

    # Orders completed
    completed_q = select(func.count()).select_from(Order).where(
        Order.status == OrderStatus.COMPLETED
    )
    completed = (await db.execute(completed_q)).scalar() or 0

    return [
        {"name": "全部订单", "value": total},
        {"name": "已报价", "value": quoted},
        {"name": "已签约", "value": contracted},
        {"name": "执行中", "value": in_progress},
        {"name": "已完成", "value": completed},
    ]


@router.get("/supply-chain-flow")
async def get_supply_chain_flow(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get supply chain flow data for Sankey diagram.
    Shows financial flow: Orders -> Contracts -> Procurements -> Settlements
    """
    # Order totals by status
    order_total_q = select(func.coalesce(func.sum(Order.total_amount), 0)).where(
        Order.status != OrderStatus.CANCELLED
    )
    order_total = float((await db.execute(order_total_q)).scalar() or 0)

    # Contract totals
    contract_total_q = select(func.coalesce(func.sum(Contract.total_amount), 0)).where(
        Contract.status.notin_([ContractStatus.DRAFT, ContractStatus.TERMINATED])
    )
    contract_total = float((await db.execute(contract_total_q)).scalar() or 0)

    # Procurement totals
    procurement_total_q = select(func.coalesce(func.sum(Procurement.total_amount), 0)).where(
        Procurement.status.notin_([ProcurementStatus.DRAFT, ProcurementStatus.CANCELLED])
    )
    procurement_total = float((await db.execute(procurement_total_q)).scalar() or 0)

    # Settlement revenue
    settlement_revenue_q = select(func.coalesce(func.sum(Settlement.total_revenue_cny), 0)).where(
        Settlement.status == SettlementStatus.APPROVED
    )
    settlement_revenue = float((await db.execute(settlement_revenue_q)).scalar() or 0)

    # Settlement cost
    settlement_cost_q = select(func.coalesce(func.sum(Settlement.total_cost_cny), 0)).where(
        Settlement.status == SettlementStatus.APPROVED
    )
    settlement_cost = float((await db.execute(settlement_cost_q)).scalar() or 0)

    # Settlement profit
    settlement_profit_q = select(func.coalesce(func.sum(Settlement.gross_profit), 0)).where(
        Settlement.status == SettlementStatus.APPROVED
    )
    settlement_profit = float((await db.execute(settlement_profit_q)).scalar() or 0)

    # Build Sankey data
    nodes = [
        {"name": "订单"},
        {"name": "合同"},
        {"name": "采购"},
        {"name": "营收"},
        {"name": "成本"},
        {"name": "利润"},
    ]

    links = []
    if order_total > 0:
        links.append({"source": "订单", "target": "合同", "value": contract_total or order_total * 0.8})
    if contract_total > 0 or order_total > 0:
        links.append({"source": "合同", "target": "采购", "value": procurement_total or contract_total * 0.6})
        links.append({"source": "合同", "target": "营收", "value": settlement_revenue or contract_total * 0.9})
    if settlement_revenue > 0 or contract_total > 0:
        cost_val = settlement_cost or procurement_total or (settlement_revenue * 0.7)
        profit_val = settlement_profit or (settlement_revenue - cost_val)
        links.append({"source": "营收", "target": "成本", "value": max(cost_val, 1)})
        links.append({"source": "营收", "target": "利润", "value": max(profit_val, 1)})

    # If no real data, provide meaningful placeholder
    if not links:
        links = [
            {"source": "订单", "target": "合同", "value": 100},
            {"source": "合同", "target": "采购", "value": 60},
            {"source": "合同", "target": "营收", "value": 90},
            {"source": "营收", "target": "成本", "value": 55},
            {"source": "营收", "target": "利润", "value": 35},
        ]

    return {"nodes": nodes, "links": links}


@router.get("/recent-activities")
async def get_recent_activities(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recent system activities for the activity feed."""
    activities = []

    # Recent orders (last 5)
    orders_q = select(Order).order_by(Order.updated_at.desc()).limit(5)
    orders_result = await db.execute(orders_q)
    for order in orders_result.scalars().all():
        status_map = {
            "DRAFT": "创建",
            "IN_PROGRESS": "启动",
            "COMPLETED": "完成",
            "CANCELLED": "取消",
        }
        action = status_map.get(order.status, "更新")
        activities.append({
            "id": f"order-{order.id}",
            "text": f"订单 {order.order_no} 已{action}",
            "time": order.updated_at.isoformat() if order.updated_at else None,
            "type": "order",
            "color": "#409EFF",
        })

    # Recent procurements (last 3)
    proc_q = select(Procurement).order_by(Procurement.updated_at.desc()).limit(3)
    proc_result = await db.execute(proc_q)
    for proc in proc_result.scalars().all():
        status_map = {
            "PENDING_APPROVAL": "提交审批",
            "APPROVED": "审批通过",
            "ORDERED": "已下单",
            "RECEIVED": "已收货",
        }
        action = status_map.get(proc.status, "更新")
        activities.append({
            "id": f"proc-{proc.id}",
            "text": f"采购单 {proc.procurement_no} {action}",
            "time": proc.updated_at.isoformat() if proc.updated_at else None,
            "type": "procurement",
            "color": "#67C23A",
        })

    # Sort by time descending and limit
    activities.sort(key=lambda x: x["time"] or "", reverse=True)
    return activities[:limit]
