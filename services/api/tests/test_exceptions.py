"""Exception handler tests."""
import pytest

from app.core.exceptions import (
    BusinessError,
    NotFoundError,
    ForbiddenError,
    ConflictError,
    InvalidStateTransitionError,
    ValidationError,
)


class TestBusinessError:
    def test_base_error(self):
        err = BusinessError(code="TEST", message="test error", status_code=400)
        assert err.code == "TEST"
        assert err.message == "test error"
        assert err.status_code == 400
        assert str(err) == "test error"
    
    def test_not_found_error(self):
        err = NotFoundError("订单", 123)
        assert err.status_code == 404
        assert "不存在" in err.message
        assert err.detail == "订单 (id=123)"
    
    def test_forbidden_error(self):
        err = ForbiddenError()
        assert err.status_code == 403
        assert "无权" in err.message
    
    def test_conflict_error(self):
        err = ConflictError("只能修改草稿状态")
        assert err.status_code == 409
        assert "草稿" in err.message
    
    def test_invalid_state_transition(self):
        err = InvalidStateTransitionError("订单", "DRAFT", "COMPLETED")
        assert err.status_code == 400
        assert "DRAFT" in err.message
        assert "COMPLETED" in err.message
    
    def test_validation_error(self):
        err = ValidationError("邮箱格式不正确", field="email")
        assert err.status_code == 422
        assert "EMAIL" in err.code
