"""
Settlement Service — Business logic for settlement and cost management.
"""
import datetime
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.settlement import Settlement, CostItem, SettlementStatus
from app.models.order import Order, Currency
from app.models.contract import Contract, PaymentRecord
from app.models.procurement import Disbursement
from app.models.user import User, UserRole
from app.core.exceptions import (
    NotFoundError,
    ForbiddenError,
    ConflictError,
)
from app.services.base import BaseService


class SettlementService(BaseService[Settlement]):
    def __init__(self):
        super().__init__(Settlement)

    @staticmethod
    def generate_settlement_no() -> str:
        today = datetime.date.today()
        ts = int(datetime.datetime.now().timestamp() * 1000) % 10000
        return f"SET{today.strftime('%Y%m%d')}{ts:04d}"

    async def list_settlements(
        self,
        db: AsyncSession,
        *,
        keyword: Optional[str] = None,
        status: Optional[SettlementStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[Settlement], int]:
        query = select(Settlement)
        if keyword:
            query = query.where(Settlement.settlement_no.ilike(f"%{keyword}%"))
        if status:
            query = query.where(Settlement.status == status)
        query = query.order_by(Settlement.created_at.desc())
        return await self.list_paginated(db, query=query, page=page, size=size)

    async def compute_financials(self, db: AsyncSession, order_id: int) -> dict:
        """Compute financial summary for an order."""
        order = (
            await db.execute(select(Order).where(Order.id == order_id))
        ).scalar_one_or_none()
        if not order:
            raise NotFoundError("订单", order_id)

        total_revenue = order.total_amount

        total_received = (
            await db.execute(
                select(func.sum(PaymentRecord.amount_cny)).where(
                    PaymentRecord.order_id == order_id
                )
            )
        ).scalar() or Decimal("0")

        total_cost = (
            await db.execute(
                select(func.sum(CostItem.amount_cny)).where(
                    CostItem.order_id == order_id
                )
            )
        ).scalar() or Decimal("0")

        total_disbursed = (
            await db.execute(
                select(func.sum(Disbursement.amount_cny)).where(
                    Disbursement.order_id == order_id
                )
            )
        ).scalar() or Decimal("0")

        gross_profit = total_revenue - total_cost
        gross_profit_rate = (
            (gross_profit / total_revenue * 100) if total_revenue > 0 else Decimal("0")
        )
        received_percentage = (
            (total_received / total_revenue * 100)
            if total_revenue > 0
            else Decimal("0")
        )

        return {
            "order": order,
            "total_revenue": total_revenue,
            "total_received": total_received,
            "total_cost": total_cost,
            "total_disbursed": total_disbursed,
            "gross_profit": gross_profit,
            "gross_profit_rate": gross_profit_rate,
            "received_percentage": received_percentage,
        }

    async def calculate_breakeven(self, db: AsyncSession, order_id: int) -> dict:
        """Calculate break-even point for an order: minimum revenue to cover costs."""
        total_cost = (
            await db.execute(
                select(func.sum(CostItem.amount_cny)).where(CostItem.order_id == order_id)
            )
        ).scalar() or Decimal("0")

        total_disbursed = (
            await db.execute(
                select(func.sum(Disbursement.amount_cny)).where(Disbursement.order_id == order_id)
            )
        ).scalar() or Decimal("0")

        all_costs = total_cost + total_disbursed
        tax_rate = Decimal("0.06")
        breakeven_revenue = all_costs / (Decimal("1") - tax_rate) if tax_rate < 1 else all_costs

        return {
            "order_id": order_id,
            "total_cost": float(total_cost),
            "total_disbursed": float(total_disbursed),
            "all_costs": float(all_costs),
            "tax_rate": float(tax_rate),
            "breakeven_revenue": float(breakeven_revenue),
        }

    async def submit(self, db: AsyncSession, settlement_id: int) -> Settlement:
        settlement = await self.get_by_id(db, settlement_id)
        if settlement.status != SettlementStatus.DRAFT:
            raise ConflictError("只能提交草稿状态的结项")
        settlement.status = SettlementStatus.PENDING_APPROVAL
        await db.flush()
        return settlement

    async def approve(
        self,
        db: AsyncSession,
        settlement_id: int,
        current_user: User,
        approved: bool,
        reject_reason: Optional[str] = None,
    ) -> Settlement:
        if current_user.role not in (UserRole.OWNER, UserRole.FIN):
            raise ForbiddenError("无权审批结项")

        settlement = await self.get_by_id(db, settlement_id)
        if settlement.status != SettlementStatus.PENDING_APPROVAL:
            raise ConflictError("只能审批待审批状态的结项")

        if approved:
            settlement.status = SettlementStatus.APPROVED
        else:
            settlement.status = SettlementStatus.REJECTED
            settlement.reject_reason = reject_reason

        settlement.approver_id = current_user.id
        settlement.approve_date = datetime.date.today()
        await db.flush()

        if approved:
            self._trigger_kingdee_sync(settlement.id)

        return settlement

    @staticmethod
    def _trigger_kingdee_sync(settlement_id: int) -> None:
        try:
            from app.core.config import settings
            if settings.KINGDEE_ENABLED:
                from app.tasks.kingdee_tasks import sync_settlement_to_jdy
                sync_settlement_to_jdy.delay(settlement_id)
        except Exception:
            pass


# Singleton
settlement_service = SettlementService()
