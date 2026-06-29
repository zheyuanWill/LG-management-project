
"""
Audit Log Schemas
"""
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from app.models.audit_log import AuditLogAction, AuditLogObjectType


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: int
    user_id: int
    user_name: Optional[str] = None
    action: AuditLogAction
    object_type: AuditLogObjectType
    object_id: int
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    remarks: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

