"""
Order Service — Business logic for orders and quotes.

Encapsulates validation, state transitions, and business rules
that were previously scattered across router handlers.
"""
import datetime
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from sqlalchemy import select as sa_select

from app.models.order import Order, OrderLineItem, OrderStatus
from app.models.customer import Customer, Vessel
from app.models.user import User, UserRole
from app.core.exceptions import (
    NotFoundError,
    ForbiddenError,
    InvalidStateTransitionError,
    ConflictError,
)
from app.services.base import BaseService


# Valid state transitions
ORDER_TRANSITIONS = {
    OrderStatus.INQUIRY: [OrderStatus.DRAFT, OrderStatus.CANCELLED],
    OrderStatus.DRAFT: [OrderStatus.IN_PROGRESS, OrderStatus.CANCELLED],
    OrderStatus.IN_PROGRESS: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
    OrderStatus.COMPLETED: [],
    OrderStatus.CANCELLED: [],
}


class OrderService(BaseService[Order]):
    def __init__(self):
        super().__init__(Order)

    @staticmethod
    def generate_order_no() -> str:
        today = datetime.date.today()
        ts = int(datetime.datetime.now().timestamp() * 1000) % 10000
        return f"ORD{today.strftime('%Y%m%d')}{ts:04d}"

    async def create_inquiry(
        self,
        db: AsyncSession,
        *,
        current_user: User,
        customer_id: int,
        vessel_id: Optional[int] = None,
        project_type: str,
        currency: str = "CNY",
        inquiry_source: Optional[str] = None,
        delivery_date=None,
        notes: Optional[str] = None,
        line_items_data: list = None,
    ) -> Order:
        """Create an order in INQUIRY status with RFQ number."""
        from app.services.number_service import generate_inquiry_no
        order_no = self.generate_order_no()
        inquiry_no = await generate_inquiry_no(db, project_type)
        total_amount = Decimal("0")

        order = Order(
            order_no=order_no,
            inquiry_no=inquiry_no,
            customer_id=customer_id,
            vessel_id=vessel_id,
            project_type=project_type,
            currency=currency,
            delivery_date=delivery_date,
            inquiry_source=inquiry_source,
            notes=notes,
            pm_id=current_user.id,
            status=OrderStatus.INQUIRY,
            total_amount=total_amount,
        )
        db.add(order)
        await db.flush()

        for item_data in (line_items_data or []):
            amount = item_data.quantity * item_data.unit_price
            total_amount += amount
            db.add(OrderLineItem(
                order_id=order.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                specification=item_data.specification,
                unit=item_data.unit,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                amount=amount,
                notes=item_data.notes,
            ))

        order.total_amount = total_amount
        await db.commit()
        await db.refresh(order)
        return order

    async def promote_to_project(
        self,
        db: AsyncSession,
        order_id: int,
    ) -> Order:
        """Generate project_code when customer accepts quote."""
        from app.services.number_service import generate_project_code
        order = await self.get_by_id(db, order_id)
        if not order.project_code:
            order.project_code = await generate_project_code(db, order.project_type)
        await db.commit()
        await db.refresh(order)
        self._trigger_kingdee_sync(order_id)
        return order

    async def list_orders(
        self,
        db: AsyncSession,
        *,
        current_user: User,
        keyword: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        project_type=None,
        customer_id: Optional[int] = None,
        pm_id: Optional[int] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[Order], int]:
        query = select(Order)

        # Role-based filtering
        if current_user.role not in (UserRole.OWNER, UserRole.FIN):
            query = query.where(Order.pm_id == current_user.id)

        if keyword:
            query = query.outerjoin(Customer, Order.customer_id == Customer.id).where(
                Order.order_no.ilike(f"%{keyword}%")
                | Customer.name.ilike(f"%{keyword}%")
            )
        if status:
            query = query.where(Order.status == status)
        if project_type:
            query = query.where(Order.project_type == project_type)
        if customer_id:
            query = query.where(Order.customer_id == customer_id)
        if pm_id:
            query = query.where(Order.pm_id == pm_id)

        query = query.order_by(Order.created_at.desc())
        return await self.list_paginated(db, query=query, page=page, size=size)

    async def get_order_detail(self, db: AsyncSession, order_id: int) -> dict:
        """Get order with all related information."""
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.line_items))
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            raise NotFoundError("订单", order_id)

        # Load related entities
        customer = (await db.execute(
            select(Customer).where(Customer.id == order.customer_id)
        )).scalar_one_or_none()

        vessel = None
        if order.vessel_id:
            vessel = (await db.execute(
                select(Vessel).where(Vessel.id == order.vessel_id)
            )).scalar_one_or_none()

        pm = (await db.execute(
            select(User).where(User.id == order.pm_id)
        )).scalar_one_or_none()

        return {
            "order": order,
            "customer_name": customer.name if customer else None,
            "vessel_name": vessel.name if vessel else None,
            "pm_name": pm.real_name if pm else None,
        }

    async def create_order(
        self,
        db: AsyncSession,
        *,
        current_user: User,
        customer_id: int,
        vessel_id: Optional[int] = None,
        project_type: str,
        currency: str = "CNY",
        delivery_date=None,
        notes: Optional[str] = None,
        line_items_data: list = None,
    ) -> Order:
        order_no = self.generate_order_no()
        total_amount = Decimal("0")

        order = Order(
            order_no=order_no,
            customer_id=customer_id,
            vessel_id=vessel_id,
            project_type=project_type,
            currency=currency,
            delivery_date=delivery_date,
            notes=notes,
            pm_id=current_user.id,
            status=OrderStatus.DRAFT,
            total_amount=total_amount,
        )
        db.add(order)
        await db.flush()

        for item_data in (line_items_data or []):
            amount = item_data.quantity * item_data.unit_price
            total_amount += amount
            db.add(OrderLineItem(
                order_id=order.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                specification=item_data.specification,
                unit=item_data.unit,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                amount=amount,
                notes=item_data.notes,
            ))

        order.total_amount = total_amount
        await db.commit()
        await db.refresh(order)
        return order

    async def update_order(
        self,
        db: AsyncSession,
        order_id: int,
        current_user: User,
        data: dict,
    ) -> Order:
        order = await self.get_by_id(db, order_id)

        if order.pm_id != current_user.id and current_user.role != UserRole.OWNER:
            raise ForbiddenError("无权修改此订单")

        if order.status != OrderStatus.DRAFT:
            raise ConflictError("只能修改草稿状态的订单")

        for key, value in data.items():
            if value is not None:
                setattr(order, key, value)

        await db.commit()
        await db.refresh(order)
        return order

    async def update_status(
        self,
        db: AsyncSession,
        order_id: int,
        new_status: OrderStatus,
        operator_id: Optional[int] = None,
        cancellation_reason: Optional[str] = None,
        cancellation_category: Optional[str] = None,
    ) -> Order:
        order = await self.get_by_id(db, order_id)

        allowed = ORDER_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise InvalidStateTransitionError("订单", str(order.status.value), str(new_status.value))

        order.status = new_status
        if new_status == OrderStatus.CANCELLED:
            if cancellation_reason:
                order.cancellation_reason = cancellation_reason
            if cancellation_category:
                order.cancellation_category = cancellation_category

        await db.commit()
        await db.refresh(order)

        if new_status == OrderStatus.IN_PROGRESS:
            self._trigger_kingdee_sync(order_id)
            await self._auto_create_workflow(db, order, operator_id)

        # Notify workflow engine of status change
        await self._notify_workflow(db, order, new_status, operator_id)

        return order

    @staticmethod
    async def _auto_create_workflow(
        db: AsyncSession, order: Order, operator_id: Optional[int]
    ) -> None:
        """Auto-create a workflow instance when order starts."""
        try:
            from app.services.workflow_hooks import auto_create_workflow_for_order
            await auto_create_workflow_for_order(
                db,
                order_id=order.id,
                project_type=order.project_type or "",
                started_by=operator_id or order.pm_id,
            )
        except Exception:
            pass

    @staticmethod
    async def _notify_workflow(
        db: AsyncSession, order: Order, new_status: OrderStatus, operator_id: Optional[int]
    ) -> None:
        """Notify workflow engine when order status changes."""
        try:
            from app.services.workflow_hooks import on_entity_status_change
            await on_entity_status_change(
                db,
                entity_type="order",
                entity_id=order.id,
                new_status=new_status.value,
                order_id=order.id,
                operator_id=operator_id,
            )
        except Exception:
            pass

    @staticmethod
    def _trigger_kingdee_sync(order_id: int) -> None:
        """Fire-and-forget Celery task for Kingdee synchronisation."""
        try:
            from app.core.config import settings
            if settings.KINGDEE_ENABLED:
                from app.tasks.kingdee_tasks import sync_order_to_jdy
                sync_order_to_jdy.delay(order_id)
        except Exception:
            pass

    async def add_line_item(
        self,
        db: AsyncSession,
        order_id: int,
        data,
    ) -> OrderLineItem:
        """添加订单明细（仅草稿状态）"""
        order = await self.get_by_id(db, order_id)

        if order.status != OrderStatus.DRAFT:
            raise ConflictError("只能在草稿状态添加明细")

        amount = data.quantity * data.unit_price
        line_item = OrderLineItem(
            order_id=order_id,
            product_id=data.product_id,
            product_name=data.product_name,
            specification=data.specification,
            unit=data.unit,
            quantity=data.quantity,
            unit_price=data.unit_price,
            amount=amount,
            notes=data.notes,
        )
        db.add(line_item)
        order.total_amount += amount
        await db.commit()
        await db.refresh(line_item)
        return line_item

    async def delete_line_item(
        self,
        db: AsyncSession,
        order_id: int,
        item_id: int,
    ) -> dict:
        """删除订单明细（仅草稿状态）"""
        order = await self.get_by_id(db, order_id)

        if order.status != OrderStatus.DRAFT:
            raise ConflictError("只能在草稿状态删除明细")

        item_result = await db.execute(
            sa_select(OrderLineItem).where(
                OrderLineItem.id == item_id,
                OrderLineItem.order_id == order_id,
            )
        )
        item = item_result.scalar_one_or_none()
        if not item:
            raise NotFoundError("订单明细", item_id)

        order.total_amount -= item.amount
        await db.delete(item)
        await db.commit()
        return {"message": "删除成功"}


# Singleton
order_service = OrderService()
