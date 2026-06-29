"""Notification Router"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from app.core.exceptions import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate, NotificationResponse, NotificationUpdate
from app.schemas.common import PageResponse

router = APIRouter(prefix="/notifications", tags=["消息通知"])


@router.get("", response_model=PageResponse[NotificationResponse])
async def list_notifications(
    type: Optional[NotificationType] = Query(None),
    is_read: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的通知列表"""
    query = select(Notification).where(Notification.user_id == current_user.id)
    
    if type:
        query = query.where(Notification.type == type)
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
    
    query = query.order_by(Notification.created_at.desc())
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0
    
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PageResponse.create(items=items, total=total, page=page, size=size)


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取未读消息数量"""
    result = await db.execute(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == current_user.id)
        .where(Notification.is_read == False)
    )
    count = result.scalar() or 0
    return {"count": count}


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记单条消息为已读"""
    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == current_user.id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("通知", notification_id)
    
    notification.is_read = True
    notification.read_at = datetime.now()
    await db.commit()
    await db.refresh(notification)
    return notification


@router.put("/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """标记全部消息为已读"""
    await db.execute(
        update(Notification)
        .where(Notification.user_id == current_user.id)
        .where(Notification.is_read == False)
        .values(is_read=True, read_at=datetime.now())
    )
    await db.commit()
    return {"message": "已全部标记为已读"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除通知"""
    result = await db.execute(
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == current_user.id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("通知", notification_id)
    
    await db.delete(notification)
    await db.commit()
    return {"message": "删除成功"}


# Internal function to create notifications
async def create_notification(
    db: AsyncSession,
    user_id: int,
    type: NotificationType,
    title: str,
    content: str,
    related_type: Optional[str] = None,
    related_id: Optional[int] = None
):
    """创建通知（内部使用）"""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        related_type=related_type,
        related_id=related_id
    )
    db.add(notification)
    await db.flush()
    return notification
