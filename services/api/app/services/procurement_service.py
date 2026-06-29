"""
Procurement Service — Business logic for procurement, approval, receiving, and disbursements.
"""
import datetime
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.procurement import (
    Procurement,
    ProcurementLineItem,
    Disbursement,
    ProcurementStatus,
)
from app.models.product import Supplier
from app.models.order import Order
from app.models.inventory import InventoryBatch, InventoryMovement, InventoryMovementType
from app.models.user import User, UserRole
from app.core.exceptions import (
    NotFoundError,
    ForbiddenError,
    ConflictError,
)
from app.services.base import BaseService


class ProcurementService(BaseService[Procurement]):
    def __init__(self):
        super().__init__(Procurement)

    @staticmethod
    def generate_procurement_no() -> str:
        today = datetime.date.today()
        ts = int(datetime.datetime.now().timestamp() * 1000) % 10000
        return f"PO{today.strftime('%Y%m%d')}{ts:04d}"

    async def list_procurements(
        self,
        db: AsyncSession,
        *,
        current_user: User,
        keyword: Optional[str] = None,
        status: Optional[ProcurementStatus] = None,
        supplier_id: Optional[int] = None,
        order_id: Optional[int] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[Procurement], int]:
        query = select(Procurement)

        if current_user.role == UserRole.PROC:
            query = query.where(Procurement.created_by == current_user.id)

        if keyword:
            query = query.where(Procurement.procurement_no.ilike(f"%{keyword}%"))
        if status:
            query = query.where(Procurement.status == status)
        if supplier_id:
            query = query.where(Procurement.supplier_id == supplier_id)
        if order_id:
            query = query.where(Procurement.order_id == order_id)

        query = query.order_by(Procurement.created_at.desc())
        return await self.list_paginated(db, query=query, page=page, size=size)

    async def submit(self, db: AsyncSession, procurement_id: int) -> Procurement:
        procurement = await self.get_by_id(db, procurement_id)
        if procurement.status != ProcurementStatus.DRAFT:
            raise ConflictError("只能提交草稿状态的采购单")
        procurement.status = ProcurementStatus.PENDING_APPROVAL
        await db.flush()
        return procurement

    async def approve(
        self,
        db: AsyncSession,
        procurement_id: int,
        current_user: User,
        approved: bool,
    ) -> Procurement:
        if current_user.role not in (UserRole.OWNER, UserRole.PM):
            raise ForbiddenError("无权审批采购单")

        procurement = await self.get_by_id(db, procurement_id)
        if procurement.status != ProcurementStatus.PENDING_APPROVAL:
            raise ConflictError("只能审批待审批状态的采购单")

        if approved:
            procurement.status = ProcurementStatus.APPROVED
            procurement.approved_by = current_user.id
            procurement.approved_at = datetime.date.today()
        else:
            procurement.status = ProcurementStatus.DRAFT

        await db.flush()
        return procurement

    async def mark_ordered(self, db: AsyncSession, procurement_id: int) -> Procurement:
        procurement = await self.get_by_id(db, procurement_id)
        if procurement.status != ProcurementStatus.APPROVED:
            raise ConflictError("只能将已审批状态的采购单标记为已下单")
        procurement.status = ProcurementStatus.ORDERED
        await db.flush()
        return procurement

    async def receive(
        self,
        db: AsyncSession,
        procurement_id: int,
        current_user: User,
        items: list[dict],
    ) -> Procurement:
        if current_user.role not in (UserRole.OPS, UserRole.OWNER):
            raise ForbiddenError("无权收货")

        result = await db.execute(
            select(Procurement)
            .options(selectinload(Procurement.line_items))
            .where(Procurement.id == procurement_id)
        )
        procurement = result.scalar_one_or_none()
        if not procurement:
            raise NotFoundError("采购单", procurement_id)

        if procurement.status not in (
            ProcurementStatus.ORDERED,
            ProcurementStatus.PARTIAL_RECEIVED,
        ):
            raise ConflictError("只能对已下单或部分收货状态的采购单收货")

        batch_no = f"BATCH{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        all_received = True

        for receive_item in items:
            line_item_id = receive_item.get("line_item_id")
            quantity = Decimal(str(receive_item.get("quantity", 0)))

            line_item = next(
                (li for li in procurement.line_items if li.id == line_item_id), None
            )
            if not line_item:
                continue

            line_item.received_quantity += quantity
            if line_item.received_quantity < line_item.quantity:
                all_received = False

            db.add(
                InventoryBatch(
                    product_id=line_item.product_id,
                    batch_no=batch_no,
                    quantity=quantity,
                    unit_cost=line_item.unit_price,
                    currency=procurement.currency,
                    procurement_id=procurement.id,
                )
            )
            db.add(
                InventoryMovement(
                    product_id=line_item.product_id,
                    type=InventoryMovementType.IN,
                    quantity=quantity,
                    procurement_id=procurement.id,
                    order_id=procurement.order_id,
                    operator_id=current_user.id,
                    notes=f"采购入库 - {procurement.procurement_no}",
                )
            )

        procurement.status = (
            ProcurementStatus.RECEIVED if all_received else ProcurementStatus.PARTIAL_RECEIVED
        )
        await db.flush()

        self._trigger_kingdee_receive_sync(procurement.id)

        return procurement

    async def create_disbursement(
        self,
        db: AsyncSession,
        procurement_id: int,
        current_user: User,
        **kwargs,
    ) -> Disbursement:
        if current_user.role not in (UserRole.FIN, UserRole.OWNER):
            raise ForbiddenError("无权录入付款")

        await self.get_by_id(db, procurement_id)

        disbursement = Disbursement(procurement_id=procurement_id, **kwargs)
        db.add(disbursement)
        await db.flush()

        self._trigger_kingdee_disbursement_sync(disbursement.id)

        return disbursement

    @staticmethod
    def _trigger_kingdee_receive_sync(procurement_id: int) -> None:
        try:
            from app.core.config import settings
            if settings.KINGDEE_ENABLED:
                from app.tasks.kingdee_tasks import sync_procurement_to_jdy
                sync_procurement_to_jdy.delay(procurement_id)
        except Exception:
            pass

    @staticmethod
    def _trigger_kingdee_disbursement_sync(disbursement_id: int) -> None:
        try:
            from app.core.config import settings
            if settings.KINGDEE_ENABLED:
                from app.tasks.kingdee_tasks import sync_disbursement_to_jdy
                sync_disbursement_to_jdy.delay(disbursement_id)
        except Exception:
            pass


# Singleton
procurement_service = ProcurementService()
