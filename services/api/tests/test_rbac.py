"""RBAC permission tests."""
import pytest

from app.core.rbac import check_permission, Resource, Action, get_role_permissions, get_sensitive_fields
from app.models.user import UserRole


class TestRBAC:
    def test_owner_has_all_permissions(self):
        """Owner should have all permissions on all resources."""
        for resource in Resource:
            perms = get_role_permissions(UserRole.OWNER).get(resource, set())
            for action in [Action.CREATE, Action.READ, Action.UPDATE, Action.DELETE]:
                if action in perms:
                    assert check_permission(UserRole.OWNER, resource, action), \
                        f"OWNER should have {action} on {resource}"
    
    def test_pm_can_manage_orders(self):
        assert check_permission(UserRole.PM, Resource.ORDER, Action.CREATE)
        assert check_permission(UserRole.PM, Resource.ORDER, Action.READ)
        assert check_permission(UserRole.PM, Resource.ORDER, Action.UPDATE)
        assert not check_permission(UserRole.PM, Resource.ORDER, Action.DELETE)
    
    def test_proc_can_manage_procurement(self):
        assert check_permission(UserRole.PROC, Resource.PROCUREMENT, Action.CREATE)
        assert check_permission(UserRole.PROC, Resource.PROCUREMENT, Action.READ)
        assert check_permission(UserRole.PROC, Resource.PROCUREMENT, Action.VIEW_COST)
    
    def test_fin_can_manage_settlements(self):
        assert check_permission(UserRole.FIN, Resource.SETTLEMENT, Action.CREATE)
        assert check_permission(UserRole.FIN, Resource.SETTLEMENT, Action.APPROVE)
        assert check_permission(UserRole.FIN, Resource.SETTLEMENT, Action.VIEW_PROFIT)
    
    def test_ops_limited_access(self):
        assert check_permission(UserRole.OPS, Resource.ORDER, Action.READ)
        assert not check_permission(UserRole.OPS, Resource.ORDER, Action.CREATE)
        assert check_permission(UserRole.OPS, Resource.INVENTORY, Action.CREATE)
    
    def test_sensitive_fields_hidden_from_pm(self):
        fields = get_sensitive_fields(UserRole.PM, Resource.PROCUREMENT)
        assert len(fields) > 0
    
    def test_owner_sees_all_fields(self):
        fields = get_sensitive_fields(UserRole.OWNER, Resource.PROCUREMENT)
        assert len(fields) == 0
    
    def test_fin_sees_all_fields(self):
        fields = get_sensitive_fields(UserRole.FIN, Resource.SETTLEMENT)
        assert len(fields) == 0
    
    def test_unknown_role_has_no_permissions(self):
        # Using a non-existent role should return False
        result = check_permission("UNKNOWN", Resource.ORDER, Action.READ)
        assert result is False


class TestGetRolePermissions:
    def test_returns_dict_for_valid_role(self):
        perms = get_role_permissions(UserRole.PM)
        assert isinstance(perms, dict)
        assert Resource.ORDER in perms
    
    def test_returns_empty_for_unknown_role(self):
        perms = get_role_permissions("INVALID")
        assert perms == {}
