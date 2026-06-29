"""
Role-Based Access Control (RBAC) Configuration

Defines permissions for each role across different resources and actions.
This is the backend enforcement layer - frontend uses packages/core/rbac for UI.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Set

from fastapi import HTTPException, Depends, status

from app.models.user import UserRole

if TYPE_CHECKING:
    from app.models.user import User


class Action(str, Enum):
    """Available actions for resources"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    APPROVE = "approve"
    EXPORT = "export"
    VIEW_COST = "view_cost"  # 查看成本详情
    VIEW_PROFIT = "view_profit"  # 查看利润详情


class Resource(str, Enum):
    """Available resources"""
    ORDER = "order"
    QUOTE = "quote"
    CONTRACT = "contract"
    PROCUREMENT = "procurement"
    SUPPLIER = "supplier"
    PRODUCT = "product"
    INVENTORY = "inventory"
    TRACKING = "tracking"
    SETTLEMENT = "settlement"
    COST = "cost"
    REPORT = "report"
    USER = "user"
    FILE = "file"
    CUSTOMER_VISIT = "customer_visit"
    SHIPOWNER_BACKGROUND = "shipowner_background"
    SHIPYARD_INQUIRY = "shipyard_inquiry"
    REPAIR_PLAN = "repair_plan"
    DAILY_REPORT = "daily_report"
    PHOTO_EVIDENCE = "photo_evidence"
    ANOMALY = "anomaly"
    NCR = "ncr"
    SPARE_PART_RISK = "spare_part_risk"
    SUPPLIER_FEEDBACK = "supplier_feedback"
    RISK_DASHBOARD = "risk_dashboard"
    ISO_ARCHIVE = "iso_archive"
    PROJECT_REVIEW = "project_review"


# Permission matrix: role -> resource -> actions
PERMISSIONS: Dict[UserRole, Dict[Resource, Set[Action]]] = {
    UserRole.GENERAL_MANAGER: {
        # 总经理 - 全权限
        Resource.ORDER: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.QUOTE: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.CONTRACT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.PROCUREMENT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.VIEW_COST},
        Resource.SUPPLIER: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.VIEW_COST},
        Resource.PRODUCT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        Resource.INVENTORY: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        Resource.TRACKING: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        Resource.SETTLEMENT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.COST: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.REPORT: {Action.READ, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.USER: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        Resource.FILE: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        # 新增修船模块权限
        Resource.CUSTOMER_VISIT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.SHIPOWNER_BACKGROUND: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT},
        Resource.SHIPYARD_INQUIRY: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT},
        Resource.REPAIR_PLAN: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.DAILY_REPORT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.PHOTO_EVIDENCE: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.ANOMALY: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.NCR: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT},
        Resource.SPARE_PART_RISK: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT},
        Resource.SUPPLIER_FEEDBACK: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.RISK_DASHBOARD: {Action.READ, Action.EXPORT},
        Resource.ISO_ARCHIVE: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.PROJECT_REVIEW: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
    },
    
    UserRole.SUPERVISOR: {
        # 监修岗
        Resource.ORDER: {Action.READ, Action.EXPORT},
        Resource.QUOTE: {Action.READ, Action.EXPORT},
        Resource.CONTRACT: {Action.READ, Action.EXPORT},
        Resource.PROCUREMENT: {Action.READ},
        Resource.SUPPLIER: {Action.READ},
        Resource.PRODUCT: {Action.READ},
        Resource.INVENTORY: {Action.READ},
        Resource.TRACKING: {Action.READ, Action.UPDATE},
        Resource.COST: {Action.READ},
        Resource.REPORT: {Action.READ, Action.EXPORT},
        Resource.FILE: {Action.CREATE, Action.READ, Action.UPDATE},
        # 新增修船模块权限
        Resource.CUSTOMER_VISIT: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SHIPOWNER_BACKGROUND: {Action.READ, Action.EXPORT},
        Resource.SHIPYARD_INQUIRY: {Action.READ, Action.EXPORT},
        Resource.REPAIR_PLAN: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.DAILY_REPORT: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.PHOTO_EVIDENCE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.ANOMALY: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.NCR: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SPARE_PART_RISK: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SUPPLIER_FEEDBACK: {Action.READ, Action.EXPORT},
        Resource.RISK_DASHBOARD: {Action.READ},
        Resource.ISO_ARCHIVE: {Action.READ, Action.EXPORT},
        Resource.PROJECT_REVIEW: {Action.READ, Action.EXPORT},
    },
    
    UserRole.GENERAL_AFFAIRS: {
        # 总务
        Resource.ORDER: {Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.QUOTE: {Action.READ, Action.EXPORT},
        Resource.CONTRACT: {Action.READ, Action.EXPORT},
        Resource.PROCUREMENT: {Action.CREATE, Action.READ, Action.UPDATE, Action.VIEW_COST},
        Resource.SUPPLIER: {Action.CREATE, Action.READ, Action.UPDATE, Action.VIEW_COST},
        Resource.PRODUCT: {Action.CREATE, Action.READ, Action.UPDATE},
        Resource.INVENTORY: {Action.CREATE, Action.READ, Action.UPDATE},
        Resource.TRACKING: {Action.CREATE, Action.READ, Action.UPDATE},
        Resource.COST: {Action.READ, Action.VIEW_COST},
        Resource.REPORT: {Action.READ, Action.EXPORT},
        Resource.FILE: {Action.CREATE, Action.READ, Action.UPDATE},
        # 新增修船模块权限
        Resource.CUSTOMER_VISIT: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SHIPOWNER_BACKGROUND: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SHIPYARD_INQUIRY: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.REPAIR_PLAN: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.DAILY_REPORT: {Action.READ, Action.EXPORT},
        Resource.PHOTO_EVIDENCE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.ANOMALY: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.NCR: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SPARE_PART_RISK: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SUPPLIER_FEEDBACK: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.RISK_DASHBOARD: {Action.READ},
        Resource.ISO_ARCHIVE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.PROJECT_REVIEW: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
    },
    
    UserRole.FINANCE: {
        # 财务岗
        Resource.ORDER: {Action.READ, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.QUOTE: {Action.READ, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.CONTRACT: {Action.READ, Action.UPDATE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.PROCUREMENT: {Action.READ, Action.VIEW_COST},
        Resource.SUPPLIER: {Action.READ, Action.VIEW_COST},
        Resource.PRODUCT: {Action.READ},
        Resource.INVENTORY: {Action.READ},
        Resource.TRACKING: {Action.READ},
        Resource.SETTLEMENT: {Action.CREATE, Action.READ, Action.UPDATE, Action.APPROVE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.COST: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.REPORT: {Action.READ, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.FILE: {Action.CREATE, Action.READ},
        # 新增修船模块权限
        Resource.CUSTOMER_VISIT: {Action.READ, Action.EXPORT},
        Resource.SHIPOWNER_BACKGROUND: {Action.READ, Action.EXPORT},
        Resource.SHIPYARD_INQUIRY: {Action.READ, Action.EXPORT},
        Resource.REPAIR_PLAN: {Action.READ, Action.EXPORT},
        Resource.DAILY_REPORT: {Action.READ, Action.EXPORT},
        Resource.PHOTO_EVIDENCE: {Action.READ, Action.EXPORT},
        Resource.ANOMALY: {Action.READ, Action.EXPORT},
        Resource.NCR: {Action.READ, Action.EXPORT},
        Resource.SPARE_PART_RISK: {Action.READ, Action.EXPORT},
        Resource.SUPPLIER_FEEDBACK: {Action.READ, Action.EXPORT},
        Resource.RISK_DASHBOARD: {Action.READ},
        Resource.ISO_ARCHIVE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.PROJECT_REVIEW: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
    },
    
    UserRole.SOFTWARE_ENGINEER: {
        # 软件工程师
        Resource.USER: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        Resource.FILE: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        # 系统配置、日志排查等 - 只读查看业务数据
        Resource.ORDER: {Action.READ},
        Resource.QUOTE: {Action.READ},
        Resource.CONTRACT: {Action.READ},
        Resource.PROCUREMENT: {Action.READ},
        Resource.SUPPLIER: {Action.READ},
        Resource.PRODUCT: {Action.READ},
        Resource.INVENTORY: {Action.READ},
        Resource.TRACKING: {Action.READ},
        Resource.SETTLEMENT: {Action.READ},
        Resource.COST: {Action.READ},
        Resource.REPORT: {Action.READ},
        # 新增修船模块权限 - 只读
        Resource.CUSTOMER_VISIT: {Action.READ},
        Resource.SHIPOWNER_BACKGROUND: {Action.READ},
        Resource.SHIPYARD_INQUIRY: {Action.READ},
        Resource.REPAIR_PLAN: {Action.READ},
        Resource.DAILY_REPORT: {Action.READ},
        Resource.PHOTO_EVIDENCE: {Action.READ},
        Resource.ANOMALY: {Action.READ},
        Resource.NCR: {Action.READ},
        Resource.SPARE_PART_RISK: {Action.READ},
        Resource.SUPPLIER_FEEDBACK: {Action.READ},
        Resource.RISK_DASHBOARD: {Action.READ},
        Resource.ISO_ARCHIVE: {Action.READ},
        Resource.PROJECT_REVIEW: {Action.READ},
    },
    
    # Backward compatibility
    UserRole.OWNER: {
        Resource.ORDER: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.QUOTE: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.CONTRACT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.PROCUREMENT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.VIEW_COST},
        Resource.SUPPLIER: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.VIEW_COST},
        Resource.PRODUCT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        Resource.INVENTORY: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        Resource.TRACKING: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        Resource.SETTLEMENT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.COST: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.REPORT: {Action.READ, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.USER: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        Resource.FILE: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE},
        Resource.CUSTOMER_VISIT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.SHIPOWNER_BACKGROUND: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT},
        Resource.SHIPYARD_INQUIRY: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT},
        Resource.REPAIR_PLAN: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.DAILY_REPORT: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.PHOTO_EVIDENCE: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.ANOMALY: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.NCR: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT},
        Resource.SPARE_PART_RISK: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.APPROVE, Action.EXPORT},
        Resource.SUPPLIER_FEEDBACK: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.RISK_DASHBOARD: {Action.READ, Action.EXPORT},
        Resource.ISO_ARCHIVE: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
        Resource.PROJECT_REVIEW: {Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE, Action.EXPORT},
    },
    UserRole.PM: {
        Resource.ORDER: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.QUOTE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.CONTRACT: {Action.READ, Action.UPDATE},
        Resource.PROCUREMENT: {Action.READ},
        Resource.SUPPLIER: {Action.READ},
        Resource.PRODUCT: {Action.READ},
        Resource.INVENTORY: {Action.READ},
        Resource.TRACKING: {Action.CREATE, Action.READ, Action.UPDATE},
        Resource.SETTLEMENT: {Action.CREATE, Action.READ},
        Resource.COST: {Action.READ},
        Resource.REPORT: {Action.READ},
        Resource.FILE: {Action.CREATE, Action.READ},
        Resource.CUSTOMER_VISIT: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SHIPOWNER_BACKGROUND: {Action.READ, Action.EXPORT},
        Resource.SHIPYARD_INQUIRY: {Action.READ, Action.EXPORT},
        Resource.REPAIR_PLAN: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.DAILY_REPORT: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.PHOTO_EVIDENCE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.ANOMALY: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.NCR: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SPARE_PART_RISK: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SUPPLIER_FEEDBACK: {Action.READ, Action.EXPORT},
        Resource.RISK_DASHBOARD: {Action.READ},
        Resource.ISO_ARCHIVE: {Action.READ, Action.EXPORT},
        Resource.PROJECT_REVIEW: {Action.READ, Action.EXPORT},
    },
    UserRole.PROC: {
        Resource.ORDER: {Action.READ},
        Resource.QUOTE: {Action.READ},
        Resource.CONTRACT: {Action.READ},
        Resource.PROCUREMENT: {Action.CREATE, Action.READ, Action.UPDATE, Action.VIEW_COST},
        Resource.SUPPLIER: {Action.CREATE, Action.READ, Action.UPDATE, Action.VIEW_COST},
        Resource.PRODUCT: {Action.CREATE, Action.READ, Action.UPDATE},
        Resource.INVENTORY: {Action.CREATE, Action.READ, Action.UPDATE},
        Resource.TRACKING: {Action.READ, Action.UPDATE},
        Resource.COST: {Action.READ, Action.VIEW_COST},
        Resource.FILE: {Action.CREATE, Action.READ},
        Resource.CUSTOMER_VISIT: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SHIPOWNER_BACKGROUND: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SHIPYARD_INQUIRY: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.REPAIR_PLAN: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.DAILY_REPORT: {Action.READ, Action.EXPORT},
        Resource.PHOTO_EVIDENCE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.ANOMALY: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.NCR: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SPARE_PART_RISK: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SUPPLIER_FEEDBACK: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.RISK_DASHBOARD: {Action.READ},
        Resource.ISO_ARCHIVE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.PROJECT_REVIEW: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
    },
    UserRole.OPS: {
        Resource.ORDER: {Action.READ, Action.EXPORT},
        Resource.QUOTE: {Action.READ, Action.EXPORT},
        Resource.CONTRACT: {Action.READ, Action.EXPORT},
        Resource.PROCUREMENT: {Action.READ},
        Resource.SUPPLIER: {Action.READ},
        Resource.PRODUCT: {Action.CREATE, Action.READ, Action.UPDATE},
        Resource.INVENTORY: {Action.CREATE, Action.READ, Action.UPDATE},
        Resource.TRACKING: {Action.READ},
        Resource.COST: {Action.READ},
        Resource.REPORT: {Action.READ, Action.EXPORT},
        Resource.FILE: {Action.CREATE, Action.READ},
        Resource.CUSTOMER_VISIT: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SHIPOWNER_BACKGROUND: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SHIPYARD_INQUIRY: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.REPAIR_PLAN: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.DAILY_REPORT: {Action.READ, Action.EXPORT},
        Resource.PHOTO_EVIDENCE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.ANOMALY: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.NCR: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SPARE_PART_RISK: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.SUPPLIER_FEEDBACK: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.RISK_DASHBOARD: {Action.READ},
        Resource.ISO_ARCHIVE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.PROJECT_REVIEW: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
    },
    UserRole.FIN: {
        Resource.ORDER: {Action.READ, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.QUOTE: {Action.READ, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.CONTRACT: {Action.READ, Action.UPDATE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.PROCUREMENT: {Action.READ, Action.VIEW_COST},
        Resource.SUPPLIER: {Action.READ, Action.VIEW_COST},
        Resource.PRODUCT: {Action.READ},
        Resource.INVENTORY: {Action.READ},
        Resource.TRACKING: {Action.READ},
        Resource.SETTLEMENT: {Action.CREATE, Action.READ, Action.UPDATE, Action.APPROVE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.COST: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.REPORT: {Action.READ, Action.EXPORT, Action.VIEW_COST, Action.VIEW_PROFIT},
        Resource.FILE: {Action.CREATE, Action.READ},
        Resource.CUSTOMER_VISIT: {Action.READ, Action.EXPORT},
        Resource.SHIPOWNER_BACKGROUND: {Action.READ, Action.EXPORT},
        Resource.SHIPYARD_INQUIRY: {Action.READ, Action.EXPORT},
        Resource.REPAIR_PLAN: {Action.READ, Action.EXPORT},
        Resource.DAILY_REPORT: {Action.READ, Action.EXPORT},
        Resource.PHOTO_EVIDENCE: {Action.READ, Action.EXPORT},
        Resource.ANOMALY: {Action.READ, Action.EXPORT},
        Resource.NCR: {Action.READ, Action.EXPORT},
        Resource.SPARE_PART_RISK: {Action.READ, Action.EXPORT},
        Resource.SUPPLIER_FEEDBACK: {Action.READ, Action.EXPORT},
        Resource.RISK_DASHBOARD: {Action.READ},
        Resource.ISO_ARCHIVE: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
        Resource.PROJECT_REVIEW: {Action.CREATE, Action.READ, Action.UPDATE, Action.EXPORT},
    },
}


def check_permission(role: UserRole, resource: Resource, action: Action) -> bool:
    """
    Check if a role has permission to perform an action on a resource
    
    Args:
        role: User role
        resource: Target resource
        action: Requested action
    
    Returns:
        True if permission granted, False otherwise
    """
    role_permissions = PERMISSIONS.get(role, {})
    resource_permissions = role_permissions.get(resource, set())
    return action in resource_permissions


def require_permission(resource: Resource, action: Action):
    """
    FastAPI dependency factory that requires a specific permission
    
    Usage:
        @router.get("/orders")
        async def get_orders(
            user: User = Depends(require_permission(Resource.ORDER, Action.READ))
        ):
            ...
    """
    # Import here to avoid circular imports
    from app.core.deps import get_current_user
    from app.models.user import User
    
    async def permission_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        if not check_permission(current_user.role, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {resource.value}:{action.value}"
            )
        return current_user
    
    return permission_dependency


def get_role_permissions(role: UserRole) -> Dict[Resource, Set[Action]]:
    """Get all permissions for a role"""
    return PERMISSIONS.get(role, {})


def get_sensitive_fields(role: UserRole, resource: Resource) -> List[str]:
    """
    Get list of fields that should be hidden/masked for this role
    
    Returns:
        List of field names to hide or mask
    """
    sensitive_fields = {
        Resource.PROCUREMENT: ["supplier_unit_price", "cost_breakdown"],
        Resource.SUPPLIER: ["bank_account", "contact_phone", "unit_prices"],
        Resource.COST: ["detailed_costs", "supplier_margins"],
        Resource.SETTLEMENT: ["detailed_profit", "cost_items"],
    }
    
    # GENERAL_MANAGER and FINANCE can see all fields
    if role in [UserRole.GENERAL_MANAGER, UserRole.FINANCE, UserRole.OWNER, UserRole.FIN]:
        return []
    
    # GENERAL_AFFAIRS and PROC can see procurement/supplier costs
    if role in [UserRole.GENERAL_AFFAIRS, UserRole.PROC] and resource in [Resource.PROCUREMENT, Resource.SUPPLIER]:
        return []
    
    return sensitive_fields.get(resource, [])
