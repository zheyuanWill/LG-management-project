"""Tracking Router"""
from typing import Optional, List
from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundError, ConflictError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.deps import get_db
from app.core.rbac import require_permission, Resource, Action
from app.models.user import User
from app.models.tracking import NodeTemplate, TrackingNode, NodeStatus
from app.models.order import Order, ProjectType
from app.models.file import FileAttachment, FileObjectType
from app.schemas.tracking import (
    NodeTemplateCreate, NodeTemplateUpdate, NodeTemplateResponse,
    TrackingNodeCreate, TrackingNodeUpdate, TrackingNodeResponse,
    TrackingNodeStatusUpdate, TrackingNodeDetail, InitTrackingFromTemplate
)
from app.schemas.common import PageResponse

router = APIRouter(prefix="/tracking", tags=["跟单管理"])


@router.get("/templates", response_model=List[NodeTemplateResponse])
async def list_node_templates(
    project_type: Optional[ProjectType] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.READ))
):
    """获取节点模板列表"""
    query = select(NodeTemplate)
    if project_type:
        query = query.where(NodeTemplate.project_type == project_type)
    query = query.order_by(NodeTemplate.sort_order)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/templates", response_model=NodeTemplateResponse)
async def create_node_template(
    data: NodeTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.CREATE))
):
    """创建节点模板"""
    template = NodeTemplate(**data.model_dump())
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.put("/templates/{template_id}", response_model=NodeTemplateResponse)
async def update_node_template(
    template_id: int,
    data: NodeTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.UPDATE))
):
    """更新节点模板"""
    result = await db.execute(select(NodeTemplate).where(NodeTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise NotFoundError("模板", template_id)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(template, key, value)
    
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/nodes", response_model=PageResponse[TrackingNodeResponse])
async def list_tracking_nodes(
    order_id: Optional[int] = Query(None),
    status: Optional[NodeStatus] = Query(None),
    assignee_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.READ))
):
    """获取跟单节点列表"""
    query = select(TrackingNode)
    
    if order_id:
        query = query.where(TrackingNode.order_id == order_id)
    if status:
        query = query.where(TrackingNode.status == status)
    if assignee_id:
        query = query.where(TrackingNode.assignee_id == assignee_id)
    
    query = query.order_by(TrackingNode.sort_order)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    nodes = result.scalars().all()
    
    responses = []
    for node in nodes:
        assignee = None
        if node.assignee_id:
            assignee_result = await db.execute(select(User).where(User.id == node.assignee_id))
            assignee = assignee_result.scalar_one_or_none()
        responses.append(
            TrackingNodeResponse(
                **node.__dict__,
                assignee_name=assignee.real_name if assignee else None
            )
        )
    
    return PageResponse.create(items=responses, total=total, page=page, size=size)


@router.post("/nodes", response_model=TrackingNodeResponse)
async def create_tracking_node(
    data: TrackingNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.CREATE))
):
    """创建跟单节点"""
    # Check order exists
    order = await db.execute(select(Order).where(Order.id == data.order_id))
    if not order.scalar_one_or_none():
        raise NotFoundError("订单", data.order_id)
    
    node = TrackingNode(**data.model_dump(), status=NodeStatus.PENDING)
    db.add(node)
    await db.commit()
    await db.refresh(node)

    if node.assignee_id:
        try:
            from app.routers.notification import create_notification
            from app.models.notification import NotificationType
            order_obj = (await db.execute(select(Order).where(Order.id == data.order_id))).scalar_one_or_none()
            await create_notification(
                db, user_id=node.assignee_id, type=NotificationType.INFO,
                title=f"新节点分配: {node.name}",
                content=f"订单 {order_obj.order_no if order_obj else data.order_id} 的节点「{node.name}」已分配给您",
                related_type="tracking_node", related_id=node.id,
            )
            await db.commit()
        except Exception:
            pass

    return node


@router.get("/nodes/{node_id}", response_model=TrackingNodeDetail)
async def get_tracking_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.READ))
):
    """获取跟单节点详情"""
    result = await db.execute(select(TrackingNode).where(TrackingNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise NotFoundError("节点", node_id)
    
    # Get assignee
    assignee = None
    if node.assignee_id:
        assignee_result = await db.execute(select(User).where(User.id == node.assignee_id))
        assignee = assignee_result.scalar_one_or_none()
    
    # Get attachments
    attachments_result = await db.execute(
        select(FileAttachment).where(
            FileAttachment.object_type == FileObjectType.TRACKING_NODE,
            FileAttachment.object_id == node_id
        )
    )
    attachments = attachments_result.scalars().all()
    
    return TrackingNodeDetail(
        **node.__dict__,
        assignee_name=assignee.real_name if assignee else None,
        attachments=[{"id": a.id, "file_name": a.file_name, "file_key": a.file_key} for a in attachments]
    )


@router.put("/nodes/{node_id}", response_model=TrackingNodeResponse)
async def update_tracking_node(
    node_id: int,
    data: TrackingNodeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.UPDATE))
):
    """更新跟单节点"""
    result = await db.execute(select(TrackingNode).where(TrackingNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise NotFoundError("节点", node_id)
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(node, key, value)
    
    await db.commit()
    await db.refresh(node)
    return node


@router.put("/nodes/{node_id}/status", response_model=TrackingNodeResponse)
async def update_node_status(
    node_id: int,
    data: TrackingNodeStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.UPDATE))
):
    """更新节点状态"""
    result = await db.execute(select(TrackingNode).where(TrackingNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise NotFoundError("节点", node_id)
    
    node.status = data.status
    if data.actual_date:
        node.actual_date = data.actual_date
    elif data.status == NodeStatus.COMPLETED and not node.actual_date:
        node.actual_date = date.today()
    if data.notes:
        node.notes = data.notes
    
    await db.commit()
    await db.refresh(node)

    if data.status == NodeStatus.COMPLETED and node.order_id:
        try:
            from app.models.order import OrderStatus
            all_nodes = (await db.execute(
                select(TrackingNode).where(TrackingNode.order_id == node.order_id)
            )).scalars().all()
            if all_nodes and all(n.status == NodeStatus.COMPLETED for n in all_nodes):
                order_obj = (await db.execute(
                    select(Order).where(Order.id == node.order_id)
                )).scalar_one_or_none()
                if order_obj and order_obj.status == OrderStatus.IN_PROGRESS:
                    order_obj.status = OrderStatus.COMPLETED
                    await db.commit()
        except Exception:
            pass

    return node


@router.post("/init-from-template", response_model=List[TrackingNodeResponse])
async def init_tracking_from_template(
    data: InitTrackingFromTemplate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.CREATE))
):
    """从模板初始化跟单节点"""
    # Check order exists
    order = await db.execute(select(Order).where(Order.id == data.order_id))
    order = order.scalar_one_or_none()
    if not order:
        raise NotFoundError("订单", data.order_id)
    
    # Check if nodes already exist
    existing = await db.execute(
        select(TrackingNode).where(TrackingNode.order_id == data.order_id)
    )
    if existing.scalars().first():
        raise ConflictError("订单已有跟单节点")
    
    # Get templates
    templates_result = await db.execute(
        select(NodeTemplate)
        .where(NodeTemplate.project_type == data.project_type)
        .order_by(NodeTemplate.sort_order)
    )
    templates = templates_result.scalars().all()

    if not templates:
        raise NotFoundError("项目模板")

    start_date = data.start_date or date.today()
    current_date = start_date
    nodes = []
    
    for template in templates:
        node = TrackingNode(
            order_id=data.order_id,
            template_id=template.id,
            name=template.name,
            sort_order=template.sort_order,
            planned_date=current_date,
            status=NodeStatus.PENDING
        )
        db.add(node)
        nodes.append(node)
        
        if template.default_days:
            current_date = current_date + timedelta(days=template.default_days)
    
    await db.commit()
    
    # Refresh and return
    responses = []
    for node in nodes:
        await db.refresh(node)
        responses.append(TrackingNodeResponse(**node.__dict__, assignee_name=None))
    
    return responses


@router.delete("/nodes/{node_id}")
async def delete_tracking_node(
    node_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.DELETE))
):
    """删除跟单节点"""
    result = await db.execute(select(TrackingNode).where(TrackingNode.id == node_id))
    node = result.scalar_one_or_none()
    if not node:
        raise NotFoundError("节点", node_id)
    
    await db.delete(node)
    await db.commit()
    return {"message": "删除成功"}

