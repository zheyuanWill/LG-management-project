
"""
Audit Log Service
"""
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.audit_log import AuditLog, AuditLogAction, AuditLogObjectType
from app.models.user import User


class AuditService:
    """审计日志服务"""
    
    @staticmethod
    async def log_action(
        db: AsyncSession,
        user: User,
        action: AuditLogAction,
        object_type: AuditLogObjectType,
        object_id: int,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        remarks: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """记录审计日志"""
        audit_log = AuditLog(
            user_id=user.id,
            action=action,
            object_type=object_type,
            object_id=object_id,
            old_status=old_status,
            new_status=new_status,
            old_values=old_values,
            new_values=new_values,
            remarks=remarks,
            ip_address=ip_address
        )
        db.add(audit_log)
        await db.commit()
        await db.refresh(audit_log)
        return audit_log
    
    @staticmethod
    async def get_logs(
        db: AsyncSession,
        object_type: Optional[AuditLogObjectType] = None,
        object_id: Optional[int] = None,
        limit: int = 50
    ) -> list[AuditLog]:
        """获取审计日志"""
        query = select(AuditLog)
        
        if object_type:
            query = query.where(AuditLog.object_type == object_type)
        if object_id:
            query = query.where(AuditLog.object_id == object_id)
        
        query = query.order_by(AuditLog.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()


# Singleton instance
audit_service = AuditService()

