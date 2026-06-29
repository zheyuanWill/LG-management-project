"""
Workflow Schemas — Request/response models for workflow API.
"""
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Template Schemas
# ---------------------------------------------------------------------------

class WorkflowNodeDefinition(BaseModel):
    """Node definition within a workflow template"""
    id: str
    type: str  # custom
    position: dict = Field(default_factory=lambda: {"x": 0, "y": 0})
    data: dict = Field(default_factory=dict)


class WorkflowEdgeDefinition(BaseModel):
    """Edge definition within a workflow template"""
    id: str
    source: str
    target: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    label: Optional[str] = None


class WorkflowDefinition(BaseModel):
    """Complete workflow definition (nodes + edges)"""
    nodes: list[WorkflowNodeDefinition] = Field(default_factory=list)
    edges: list[WorkflowEdgeDefinition] = Field(default_factory=list)


class WorkflowTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    project_type: Optional[str] = None
    definition: dict = Field(default_factory=dict)


class WorkflowTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    project_type: Optional[str] = None
    definition: Optional[dict] = None
    is_active: Optional[bool] = None


class WorkflowTemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    project_type: Optional[str] = None
    definition: dict = {}
    is_active: bool = True
    version: int = 1
    created_by: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowTemplateListResponse(BaseModel):
    """Template without full definition for list views"""
    id: int
    name: str
    description: Optional[str] = None
    project_type: Optional[str] = None
    is_active: bool = True
    version: int = 1
    node_count: int = 0
    edge_count: int = 0
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Instance Schemas
# ---------------------------------------------------------------------------

class WorkflowInstanceCreate(BaseModel):
    template_id: int
    order_id: Optional[int] = None
    name: Optional[str] = None


class NodeStateUpdate(BaseModel):
    node_id: str
    status: str  # PENDING, RUNNING, COMPLETED, SKIPPED, FAILED
    notes: Optional[str] = None


class WorkflowInstanceResponse(BaseModel):
    id: int
    template_id: int
    order_id: Optional[int] = None
    name: str
    status: str
    current_node_id: Optional[str] = None
    node_states: dict = {}
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    started_by: Optional[int] = None
    template_name: Optional[str] = None
    order_no: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowInstanceDetail(WorkflowInstanceResponse):
    definition: dict = {}  # Full template definition for rendering
    audit_logs: list["AuditLogResponse"] = []


# ---------------------------------------------------------------------------
# Graph Validation Schemas
# ---------------------------------------------------------------------------

class ValidationError(BaseModel):
    type: str  # "error" | "warning"
    message: str
    node_ids: list[str] = []
    edge_ids: list[str] = []


class ValidationResult(BaseModel):
    valid: bool
    errors: list[ValidationError] = []
    warnings: list[ValidationError] = []


class ValidateRequest(BaseModel):
    """Validate a workflow definition without saving"""
    definition: dict


# ---------------------------------------------------------------------------
# Condition Evaluation Schemas
# ---------------------------------------------------------------------------

class ConditionEvaluateRequest(BaseModel):
    """Evaluate a condition expression against order context"""
    expression: str
    context: dict = Field(
        default_factory=dict,
        description="Variables like amount, project_type, status, etc."
    )


class ConditionEvaluateResponse(BaseModel):
    result: bool
    expression: str
    context: dict
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Audit Log Schemas
# ---------------------------------------------------------------------------

class AuditLogResponse(BaseModel):
    id: int
    instance_id: int
    node_id: Optional[str] = None
    action: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Resolve forward references used in WorkflowInstanceDetail
WorkflowInstanceDetail.model_rebuild()
