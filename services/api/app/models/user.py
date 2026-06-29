"""
User Model
"""
from enum import Enum
from typing import Optional

from sqlalchemy import String, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserRole(str, Enum):
    """User roles for RBAC"""
    GENERAL_MANAGER = "GENERAL_MANAGER"  # 总经理 - 查看全局、审批、最终确认、风险决策
    SUPERVISOR = "SUPERVISOR"    # 监修岗 - 现场日报、计划上传、异常上报、缺备件上报、照片上传
    GENERAL_AFFAIRS = "GENERAL_AFFAIRS"  # 总务 - 供应商反馈录入、订单跟进、资料整理、节点更新
    FINANCE = "FINANCE"  # 财务岗，含财务BP - 合同、回款、成本、结项、财务审核
    SOFTWARE_ENGINEER = "SOFTWARE_ENGINEER"  # 软件工程师 - 系统配置、用户权限、模板、AI配置、日志排查
    
    # Backward compatibility aliases
    OWNER = "GENERAL_MANAGER"
    PM = "SUPERVISOR"
    PROC = "GENERAL_AFFAIRS"
    OPS = "GENERAL_AFFAIRS"
    FIN = "FINANCE"


class User(Base):
    """User model"""
    
    __tablename__ = "users"
    
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(200),
        unique=True,
        nullable=True,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    real_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, create_type=False),
        nullable=False,
        default=UserRole.OPS,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    
    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
