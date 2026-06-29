"""
Contract Service — Business logic for contracts and payments.
"""
import datetime
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.contract import Contract, PaymentPlan, PaymentRecord, ContractStatus
from app.models.order import Order
from app.models.customer import Customer
from app.models.user import User, UserRole
from app.core.exceptions import (
    NotFoundError,
    ForbiddenError,
    InvalidStateTransitionError,
    ConflictError,
)
from app.services.base import BaseService


# Valid state transitions
CONTRACT_TRANSITIONS = {
    ContractStatus.DRAFT: [ContractStatus.PENDING_APPROVAL],
    ContractStatus.PENDING_APPROVAL: [ContractStatus.EFFECTIVE, ContractStatus.DRAFT],
    ContractStatus.EFFECTIVE: [ContractStatus.EXECUTING],
    ContractStatus.EXECUTING: [ContractStatus.COMPLETED, ContractStatus.TERMINATED],
    ContractStatus.COMPLETED: [],
    ContractStatus.TERMINATED: [],
}


class ContractService(BaseService[Contract]):
    def __init__(self):
        super().__init__(Contract)

    @staticmethod
    def generate_contract_no() -> str:
        today = datetime.date.today()
        ts = int(datetime.datetime.now().timestamp() * 1000) % 10000
        return f"CON{today.strftime('%Y%m%d')}{ts:04d}"

    async def list_contracts(
        self,
        db: AsyncSession,
        *,
        keyword: Optional[str] = None,
        status: Optional[ContractStatus] = None,
        customer_id: Optional[int] = None,
        order_id: Optional[int] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[Contract], int]:
        query = select(Contract)

        if keyword:
            query = query.outerjoin(Customer, Contract.customer_id == Customer.id).where(
                Contract.contract_no.ilike(f"%{keyword}%")
                | Contract.title.ilike(f"%{keyword}%")
                | Customer.name.ilike(f"%{keyword}%")
            )
        if status:
            query = query.where(Contract.status == status)
        if customer_id:
            query = query.where(Contract.customer_id == customer_id)
        if order_id:
            query = query.where(Contract.order_id == order_id)

        query = query.order_by(Contract.created_at.desc())
        return await self.list_paginated(db, query=query, page=page, size=size)

    async def get_contract_detail(self, db: AsyncSession, contract_id: int) -> dict:
        """Get contract with payment plans and related info."""
        result = await db.execute(
            select(Contract)
            .options(selectinload(Contract.payment_plans))
            .where(Contract.id == contract_id)
        )
        contract = result.scalar_one_or_none()
        if not contract:
            raise NotFoundError("合同", contract_id)

        order = (
            await db.execute(select(Order).where(Order.id == contract.order_id))
        ).scalar_one_or_none()

        customer = (
            await db.execute(
                select(Customer).where(Customer.id == contract.customer_id)
            )
        ).scalar_one_or_none()

        return {
            "contract": contract,
            "order_no": order.order_no if order else None,
            "customer_name": customer.name if customer else None,
        }

    async def update_status(
        self,
        db: AsyncSession,
        contract_id: int,
        new_status: ContractStatus,
    ) -> Contract:
        contract = await self.get_by_id(db, contract_id)

        allowed = CONTRACT_TRANSITIONS.get(contract.status, [])
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                "合同", str(contract.status.value), str(new_status.value)
            )

        contract.status = new_status
        await db.flush()
        return contract

    async def create_payment_record(
        self,
        db: AsyncSession,
        contract_id: int,
        current_user: User,
        **kwargs,
    ) -> PaymentRecord:
        contract = await self.get_by_id(db, contract_id)

        if current_user.role not in (UserRole.FIN, UserRole.OWNER):
            raise ForbiddenError("无权录入回款")

        record = PaymentRecord(contract_id=contract_id, **kwargs)
        db.add(record)
        await db.flush()
        return record


# Singleton
contract_service = ContractService()
