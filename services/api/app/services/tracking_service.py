"""
Tracking Service — Business logic for tracking nodes and templates.
"""
from datetime import date, timedelta
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tracking import NodeTemplate, TrackingNode, NodeStatus
from app.models.order import Order, ProjectType
from app.models.user import User
from app.core.exceptions import NotFoundError, ConflictError
from app.services.base import BaseService


class TrackingService(BaseService[TrackingNode]):
    def __init__(self):
        super().__init__(TrackingNode)

    async def list_nodes(
        self,
        db: AsyncSession,
        *,
        order_id: Optional[int] = None,
        status: Optional[NodeStatus] = None,
        assignee_id: Optional[int] = None,
        page: int = 1,
        size: int = 50,
    ) -> tuple[Sequence[TrackingNode], int]:
        query = select(TrackingNode)
        if order_id:
            query = query.where(TrackingNode.order_id == order_id)
        if status:
            query = query.where(TrackingNode.status == status)
        if assignee_id:
            query = query.where(TrackingNode.assignee_id == assignee_id)
        query = query.order_by(TrackingNode.sort_order)
        return await self.list_paginated(db, query=query, page=page, size=size)

    async def update_status(
        self,
        db: AsyncSession,
        node_id: int,
        new_status: NodeStatus,
        actual_date: Optional[date] = None,
        notes: Optional[str] = None,
    ) -> TrackingNode:
        node = await self.get_by_id(db, node_id)
        node.status = new_status

        if actual_date:
            node.actual_date = actual_date
        elif new_status == NodeStatus.COMPLETED and not node.actual_date:
            node.actual_date = date.today()

        if notes:
            node.notes = notes

        await db.flush()
        return node

    async def init_from_template(
        self,
        db: AsyncSession,
        order_id: int,
        project_type: str,
        start_date: Optional[date] = None,
    ) -> list[TrackingNode]:
        # Check order exists
        order = (
            await db.execute(select(Order).where(Order.id == order_id))
        ).scalar_one_or_none()
        if not order:
            raise NotFoundError("订单", order_id)

        # Check no existing nodes
        existing = await db.execute(
            select(TrackingNode).where(TrackingNode.order_id == order_id)
        )
        if existing.scalars().first():
            raise ConflictError("订单已有跟单节点")

        # Get templates
        templates = (
            await db.execute(
                select(NodeTemplate)
                .where(NodeTemplate.project_type == project_type)
                .order_by(NodeTemplate.sort_order)
            )
        ).scalars().all()

        if not templates:
            raise NotFoundError("项目模板")

        current_date = start_date or date.today()
        nodes = []

        for template in templates:
            node = TrackingNode(
                order_id=order_id,
                template_id=template.id,
                name=template.name,
                sort_order=template.sort_order,
                planned_date=current_date,
                status=NodeStatus.PENDING,
            )
            db.add(node)
            nodes.append(node)

            if template.default_days:
                current_date = current_date + timedelta(days=template.default_days)

        await db.flush()
        return nodes


# Singleton
tracking_service = TrackingService()
