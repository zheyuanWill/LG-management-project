"""
Workflow Router — Visual workflow orchestration API.

Endpoints:
- Template CRUD
- Instance lifecycle (create, advance, list, detail)
- Graph validation
- Condition expression evaluation
- Audit log retrieval
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db
from app.core.rbac import require_permission, Resource, Action
from app.core.exceptions import NotFoundError
from app.models.user import User
from app.models.workflow import WorkflowTemplate, WorkflowInstance, WorkflowStatus
from app.models.order import Order
from app.schemas.workflow import (
    WorkflowTemplateCreate,
    WorkflowTemplateUpdate,
    WorkflowTemplateResponse,
    WorkflowTemplateListResponse,
    WorkflowInstanceCreate,
    WorkflowInstanceResponse,
    WorkflowInstanceDetail,
    NodeStateUpdate,
    ValidateRequest,
    ValidationResult,
    ConditionEvaluateRequest,
    ConditionEvaluateResponse,
    AuditLogResponse,
)
from app.schemas.common import PageResponse
from app.services.workflow_service import workflow_service, validate_workflow_definition

router = APIRouter(prefix="/workflows", tags=["工作流编排"])


# ---------------------------------------------------------------------------
# Template endpoints
# ---------------------------------------------------------------------------


@router.get("/templates", response_model=PageResponse[WorkflowTemplateListResponse])
async def list_templates(
    project_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.READ)),
):
    """获取工作流模板列表"""
    items, total = await workflow_service.list_templates(
        db, project_type=project_type, is_active=is_active, page=page, size=size
    )

    # Build list responses with node/edge counts and creator names
    user_ids = list({t.created_by for t in items if t.created_by})
    users_map: dict = {}
    if user_ids:
        from app.models.user import User as UserModel
        users_result = await db.execute(
            select(UserModel).where(UserModel.id.in_(user_ids))
        )
        users_map = {u.id: u for u in users_result.scalars().all()}

    responses = []
    for t in items:
        definition = t.definition or {}
        creator = users_map.get(t.created_by)
        responses.append(
            WorkflowTemplateListResponse(
                id=t.id,
                name=t.name,
                description=t.description,
                project_type=t.project_type,
                is_active=t.is_active,
                version=t.version,
                node_count=len(definition.get("nodes", [])),
                edge_count=len(definition.get("edges", [])),
                creator_name=creator.real_name if creator else None,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
        )

    return PageResponse.create(items=responses, total=total, page=page, size=size)


@router.post("/templates", response_model=WorkflowTemplateResponse)
async def create_template(
    data: WorkflowTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.CREATE)),
):
    """创建工作流模板"""
    template = await workflow_service.create_template(
        db,
        name=data.name,
        description=data.description,
        project_type=data.project_type,
        definition=data.definition,
        created_by=current_user.id,
    )
    await db.commit()
    await db.refresh(template)
    return WorkflowTemplateResponse(
        **template.to_dict(),
        creator_name=current_user.real_name,
    )


@router.get("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.READ)),
):
    """获取工作流模板详情"""
    template = await workflow_service.get_by_id(db, template_id)
    creator = None
    if template.created_by:
        from app.models.user import User as UserModel
        creator = (
            await db.execute(
                select(UserModel).where(UserModel.id == template.created_by)
            )
        ).scalar_one_or_none()
    return WorkflowTemplateResponse(
        **template.to_dict(),
        creator_name=creator.real_name if creator else None,
    )


@router.put("/templates/{template_id}", response_model=WorkflowTemplateResponse)
async def update_template(
    template_id: int,
    data: WorkflowTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.UPDATE)),
):
    """更新工作流模板"""
    template = await workflow_service.update_template(
        db,
        template_id,
        **data.model_dump(exclude_unset=True),
    )
    await db.commit()
    await db.refresh(template)
    return WorkflowTemplateResponse(**template.to_dict(), creator_name=None)


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.DELETE)),
):
    """删除工作流模板"""
    template = await workflow_service.get_by_id(db, template_id)
    await db.delete(template)
    await db.commit()
    return {"message": "删除成功"}


# ---------------------------------------------------------------------------
# Validation endpoint
# ---------------------------------------------------------------------------


@router.post("/validate", response_model=ValidationResult)
async def validate_definition(
    data: ValidateRequest,
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.READ)),
):
    """
    验证工作流定义的图结构.

    检查项:
    - 是否有唯一的开始和结束节点
    - 所有节点是否从开始节点可达
    - 条件节点是否有完整的 true/false 分支
    - 并行网关的 fork/join 是否合理
    """
    result = validate_workflow_definition(data.definition)
    return ValidationResult(**result)


# ---------------------------------------------------------------------------
# Condition evaluation endpoint
# ---------------------------------------------------------------------------


@router.post("/evaluate-condition", response_model=ConditionEvaluateResponse)
async def evaluate_condition(
    data: ConditionEvaluateRequest,
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.READ)),
):
    """
    测试条件表达式的求值结果.

    可用于在设计时验证条件表达式是否正确.
    支持的变量: amount, project_type, status, currency, days_elapsed
    支持的运算符: >, <, >=, <=, ==, !=, and, or, not
    """
    result, error = workflow_service.evaluate_condition(
        data.expression, data.context
    )
    return ConditionEvaluateResponse(
        result=result,
        expression=data.expression,
        context=data.context,
        error=error,
    )


# ---------------------------------------------------------------------------
# Instance endpoints
# ---------------------------------------------------------------------------


@router.post("/instances", response_model=WorkflowInstanceResponse)
async def create_instance(
    data: WorkflowInstanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.CREATE)),
):
    """为订单创建工作流实例"""
    instance = await workflow_service.create_instance(
        db,
        template_id=data.template_id,
        order_id=data.order_id,
        name=data.name,
        started_by=current_user.id,
    )
    await db.commit()
    await db.refresh(instance)

    # Get template name
    template = (
        await db.execute(
            select(WorkflowTemplate).where(
                WorkflowTemplate.id == instance.template_id
            )
        )
    ).scalar_one_or_none()

    order_no = None
    if instance.order_id:
        order = (
            await db.execute(select(Order).where(Order.id == instance.order_id))
        ).scalar_one_or_none()
        order_no = order.order_no if order else None

    return WorkflowInstanceResponse(
        **instance.to_dict(),
        template_name=template.name if template else None,
        order_no=order_no,
    )


@router.get("/instances", response_model=PageResponse[WorkflowInstanceResponse])
async def list_instances(
    order_id: Optional[int] = Query(None),
    template_id: Optional[int] = Query(None),
    status: Optional[WorkflowStatus] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.READ)),
):
    """获取工作流实例列表"""
    items, total = await workflow_service.list_instances(
        db,
        order_id=order_id,
        template_id=template_id,
        status=status,
        page=page,
        size=size,
    )

    responses = []
    for inst in items:
        responses.append(
            WorkflowInstanceResponse(**inst.to_dict(), template_name=None, order_no=None)
        )

    return PageResponse.create(items=responses, total=total, page=page, size=size)


@router.get("/instances/{instance_id}", response_model=WorkflowInstanceDetail)
async def get_instance(
    instance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.READ)),
):
    """获取工作流实例详情（含完整模板定义、审计日志）"""
    detail = await workflow_service.get_instance_detail(db, instance_id)
    instance = detail["instance"]
    template = detail["template"]

    return WorkflowInstanceDetail(
        **instance.to_dict(),
        template_name=template.name if template else None,
        order_no=detail.get("order_no"),
        definition=template.definition if template else {},
        audit_logs=detail.get("audit_logs", []),
    )


@router.put("/instances/{instance_id}/advance", response_model=WorkflowInstanceResponse)
async def advance_instance(
    instance_id: int,
    data: NodeStateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.UPDATE)),
):
    """推进工作流节点状态"""
    instance = await workflow_service.advance_node(
        db,
        instance_id,
        node_id=data.node_id,
        new_status=data.status,
        notes=data.notes,
        operator_id=current_user.id,
    )
    await db.commit()
    await db.refresh(instance)
    return WorkflowInstanceResponse(**instance.to_dict(), template_name=None, order_no=None)


# ---------------------------------------------------------------------------
# Audit log endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/instances/{instance_id}/audit-logs",
    response_model=PageResponse[AuditLogResponse],
)
async def get_audit_logs(
    instance_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Resource.TRACKING, Action.READ)),
):
    """获取工作流实例的完整审计日志"""
    logs, total = await workflow_service.get_audit_logs(db, instance_id, page, size)

    # Fetch operator names
    operator_ids = list({log.operator_id for log in logs if log.operator_id})
    operators_map: dict = {}
    if operator_ids:
        users_result = await db.execute(
            select(User).where(User.id.in_(operator_ids))
        )
        operators_map = {u.id: u for u in users_result.scalars().all()}

    responses = [
        AuditLogResponse(
            id=log.id,
            instance_id=log.instance_id,
            node_id=log.node_id,
            action=log.action,
            old_status=log.old_status,
            new_status=log.new_status,
            operator_id=log.operator_id,
            operator_name=operators_map.get(log.operator_id, None)
                          and operators_map[log.operator_id].real_name,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]

    return PageResponse.create(items=responses, total=total, page=page, size=size)
