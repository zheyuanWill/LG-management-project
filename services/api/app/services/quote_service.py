"""
Quote Service — Business logic for quotes.

Extracted from the order router to keep routing layers thin
and encapsulate business rules in a dedicated service.
"""
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, Quote, QuoteLineItem, QuoteStatus
from app.models.customer import Customer
from app.core.exceptions import NotFoundError
from app.services.base import BaseService


class QuoteService(BaseService[Quote]):
    def __init__(self):
        super().__init__(Quote)

    @staticmethod
    def generate_quote_no(order_no: str, version: int) -> str:
        """生成报价单号 (legacy fallback)"""
        return f"QT-{order_no}-V{version:02d}"

    @staticmethod
    async def generate_quote_no_iso(db, project_type) -> str:
        """生成ISO格式报价单号: QT-MT26001A"""
        from app.services.number_service import generate_quote_no
        return await generate_quote_no(db, project_type)

    async def list_quotes(
        self,
        db: AsyncSession,
        *,
        order_id: Optional[int] = None,
        status: Optional[QuoteStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[Quote], int]:
        query = select(Quote)
        if order_id:
            query = query.where(Quote.order_id == order_id)
        if status:
            query = query.where(Quote.status == status)
        query = query.order_by(Quote.created_at.desc())
        return await self.list_paginated(db, query=query, page=page, size=size)

    async def create_quote(
        self,
        db: AsyncSession,
        *,
        order_id: int,
        currency: str,
        valid_until=None,
        notes: Optional[str] = None,
        line_items_data: list,
    ) -> Quote:
        # Verify the order exists
        order_result = await db.execute(select(Order).where(Order.id == order_id))
        order = order_result.scalar_one_or_none()
        if not order:
            raise NotFoundError("订单", order_id)

        # Determine next version
        version_result = await db.execute(
            select(func.max(Quote.version)).where(Quote.order_id == order_id)
        )
        max_version = version_result.scalar() or 0
        new_version = max_version + 1

        try:
            quote_no = await self.generate_quote_no_iso(db, order.project_type)
        except Exception:
            quote_no = self.generate_quote_no(order.order_no, new_version)
        total_amount = Decimal("0")

        quote = Quote(
            quote_no=quote_no,
            order_id=order_id,
            version=new_version,
            currency=currency,
            valid_until=valid_until,
            notes=notes,
            status=QuoteStatus.DRAFT,
            total_amount=total_amount,
        )
        db.add(quote)
        await db.flush()

        for item_data in line_items_data:
            amount = item_data.quantity * item_data.unit_price
            total_amount += amount
            line_item = QuoteLineItem(
                quote_id=quote.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                specification=item_data.specification,
                unit=item_data.unit,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                amount=amount,
                notes=item_data.notes,
            )
            db.add(line_item)

        quote.total_amount = total_amount
        await db.commit()
        await db.refresh(quote)
        return quote

    async def get_quote_detail(self, db: AsyncSession, quote_id: int) -> dict:
        """Get quote with related order and customer info."""
        result = await db.execute(
            select(Quote)
            .options(selectinload(Quote.line_items))
            .where(Quote.id == quote_id)
        )
        quote = result.scalar_one_or_none()
        if not quote:
            raise NotFoundError("报价", quote_id)

        order = (
            await db.execute(select(Order).where(Order.id == quote.order_id))
        ).scalar_one_or_none()

        customer = None
        if order:
            customer = (
                await db.execute(select(Customer).where(Customer.id == order.customer_id))
            ).scalar_one_or_none()

        return {
            "quote": quote,
            "order_no": order.order_no if order else None,
            "customer_name": customer.name if customer else None,
        }

    async def update_quote_status(
        self,
        db: AsyncSession,
        quote_id: int,
        status: QuoteStatus,
        feedback: Optional[str] = None,
    ) -> Quote:
        quote = await self.get_by_id(db, quote_id)
        quote.status = status
        if feedback:
            quote.feedback = feedback
        await db.commit()
        await db.refresh(quote)
        return quote

    async def submit_for_approval(
        self,
        db: AsyncSession,
        quote_id: int,
        operator_id: int,
    ) -> dict:
        """Submit quote for approval based on gross margin tier."""
        from app.models.procurement import Disbursement
        from app.models.settlement import CostItem

        quote = await self.get_by_id(db, quote_id)
        order = (await db.execute(select(Order).where(Order.id == quote.order_id))).scalar_one()

        total_cost = (await db.execute(
            select(func.sum(CostItem.amount_cny)).where(CostItem.order_id == order.id)
        )).scalar() or Decimal("0")

        revenue = quote.total_amount
        margin = ((revenue - total_cost) / revenue * 100) if revenue > 0 else Decimal("0")

        if margin > 30:
            approval_level = "AUTO"
            quote.status = QuoteStatus.SENT
        elif margin >= 15:
            approval_level = "PM_OR_OWNER"
            quote.status = QuoteStatus.DRAFT
        else:
            approval_level = "OWNER_ONLY"
            quote.status = QuoteStatus.DRAFT

        await db.commit()
        await db.refresh(quote)
        return {
            "quote_id": quote.id,
            "gross_margin_pct": float(margin),
            "approval_level": approval_level,
            "status": quote.status.value,
        }

    async def duplicate_quote(self, db: AsyncSession, quote_id: int) -> Quote:
        """Duplicate an existing quote as a new version with incremented batch."""
        from app.services.number_service import increment_batch

        result = await db.execute(
            select(Quote)
            .options(selectinload(Quote.line_items))
            .where(Quote.id == quote_id)
        )
        source_quote = result.scalar_one_or_none()
        if not source_quote:
            raise NotFoundError("报价", quote_id)

        order = (
            await db.execute(select(Order).where(Order.id == source_quote.order_id))
        ).scalar_one_or_none()

        version_result = await db.execute(
            select(func.max(Quote.version)).where(Quote.order_id == source_quote.order_id)
        )
        max_version = version_result.scalar() or 0
        new_version = max_version + 1

        try:
            quote_no = await self.generate_quote_no_iso(db, order.project_type)
        except Exception:
            quote_no = self.generate_quote_no(order.order_no, new_version)

        # Increment batch letter: e.g. QT-MT26001A -> QT-MT26001B
        if quote_no and quote_no[-1].isalpha():
            quote_no = quote_no[:-1] + increment_batch(quote_no[-1])

        new_quote = Quote(
            quote_no=quote_no,
            order_id=source_quote.order_id,
            version=new_version,
            currency=source_quote.currency,
            total_amount=source_quote.total_amount,
            valid_until=source_quote.valid_until,
            notes=source_quote.notes,
            status=QuoteStatus.DRAFT,
        )
        db.add(new_quote)
        await db.flush()

        for item in source_quote.line_items:
            db.add(QuoteLineItem(
                quote_id=new_quote.id,
                product_id=item.product_id,
                product_name=item.product_name,
                specification=item.specification,
                unit=item.unit,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
                notes=item.notes,
            ))

        await db.commit()
        await db.refresh(new_quote)
        return new_quote


# Singleton
quote_service = QuoteService()
