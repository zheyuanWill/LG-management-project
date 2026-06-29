"""
Workflow Service — Business logic for workflow templates and instances.

Features:
- Template CRUD
- Instance lifecycle management
- Condition expression evaluation (safe AST-based parser)
- Parallel gateway (fork/join) logic
- Timer node support
- Subprocess node support
- Graph structure validation
- Audit logging for every state transition
"""
import ast
import operator
from datetime import datetime, timezone
from typing import Optional, Sequence, Any
from collections import deque

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import (
    WorkflowTemplate,
    WorkflowInstance,
    WorkflowAuditLog,
    WorkflowStatus,
    WorkflowNodeStatus,
)
from app.models.order import Order
from app.models.user import User
from app.core.exceptions import NotFoundError, ConflictError, ForbiddenError, BusinessError
from app.services.base import BaseService


# ---------------------------------------------------------------------------
# Safe expression evaluator (no eval/exec — AST only)
# ---------------------------------------------------------------------------

_ALLOWED_OPS = {
    ast.Gt: operator.gt,
    ast.Lt: operator.lt,
    ast.GtE: operator.ge,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.And: lambda a, b: a and b,
    ast.Or: lambda a, b: a or b,
    ast.Not: operator.not_,
}


def _safe_eval(expr_str: str, context: dict[str, Any]) -> bool:
    """
    Evaluate a simple expression string safely using AST parsing.

    Supports:
    - Variables from context (amount, status, project_type, etc.)
    - Comparisons: >, <, >=, <=, ==, !=
    - Boolean operators: and, or, not
    - Number and string literals

    Does NOT support:
    - Function calls
    - Attribute access
    - Subscript
    - Assignment
    """
    try:
        tree = ast.parse(expr_str.strip(), mode='eval')
    except SyntaxError as e:
        raise BusinessError(
            code="CONDITION_SYNTAX_ERROR",
            message=f"条件表达式语法错误: {e}",
        )

    def _eval_node(node: ast.expr) -> Any:
        # Literals
        if isinstance(node, ast.Constant):
            return node.value

        # Variable names
        if isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            raise BusinessError(
                code="CONDITION_UNKNOWN_VAR",
                message=f"未知变量: {node.id}",
            )

        # Comparison: a > b, a == b, etc.
        if isinstance(node, ast.Compare):
            left = _eval_node(node.left)
            for op_node, comparator in zip(node.ops, node.comparators):
                op_func = _ALLOWED_OPS.get(type(op_node))
                if op_func is None:
                    raise BusinessError(
                        code="CONDITION_UNSUPPORTED_OP",
                        message=f"不支持的比较运算符: {type(op_node).__name__}",
                    )
                right = _eval_node(comparator)
                if not op_func(left, right):
                    return False
                left = right
            return True

        # Boolean operations: and / or
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                return all(_eval_node(v) for v in node.values)
            elif isinstance(node.op, ast.Or):
                return any(_eval_node(v) for v in node.values)

        # Unary: not
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not _eval_node(node.operand)

        # Binary arithmetic
        if isinstance(node, ast.BinOp):
            op_func = _ALLOWED_OPS.get(type(node.op))
            if op_func is None:
                raise BusinessError(
                    code="CONDITION_UNSUPPORTED_OP",
                    message=f"不支持的运算符: {type(node.op).__name__}",
                )
            return op_func(_eval_node(node.left), _eval_node(node.right))

        # Expression wrapper
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)

        raise BusinessError(
            code="CONDITION_UNSUPPORTED_NODE",
            message=f"不支持的表达式节点类型: {type(node).__name__}",
        )

    result = _eval_node(tree)
    return bool(result)


# ---------------------------------------------------------------------------
# Graph Validation
# ---------------------------------------------------------------------------

def validate_workflow_definition(definition: dict) -> dict:
    """
    Validate a workflow graph structure.
    Returns { valid: bool, errors: [...], warnings: [...] }
    """
    nodes = definition.get("nodes", [])
    edges = definition.get("edges", [])
    errors = []
    warnings = []

    if not nodes:
        errors.append({
            "type": "error",
            "message": "工作流定义为空",
            "node_ids": [],
            "edge_ids": [],
        })
        return {"valid": False, "errors": errors, "warnings": warnings}

    node_map = {n.get("id"): n for n in nodes}
    out_edges: dict[str, list] = {n.get("id"): [] for n in nodes}
    in_edges: dict[str, list] = {n.get("id"): [] for n in nodes}

    for e in edges:
        src, tgt = e.get("source"), e.get("target")
        if src in node_map and tgt in node_map:
            out_edges[src].append(e)
            in_edges[tgt].append(e)

    # 1. Start node check
    start_nodes = [n for n in nodes if n.get("data", {}).get("nodeType") == "start"]
    if len(start_nodes) == 0:
        errors.append({"type": "error", "message": "缺少开始节点", "node_ids": [], "edge_ids": []})
    elif len(start_nodes) > 1:
        errors.append({
            "type": "error",
            "message": f"存在 {len(start_nodes)} 个开始节点",
            "node_ids": [n["id"] for n in start_nodes],
            "edge_ids": [],
        })

    # 2. End node check
    end_nodes = [n for n in nodes if n.get("data", {}).get("nodeType") == "end"]
    if len(end_nodes) == 0:
        errors.append({"type": "error", "message": "缺少结束节点", "node_ids": [], "edge_ids": []})
    elif len(end_nodes) > 1:
        errors.append({
            "type": "error",
            "message": f"存在 {len(end_nodes)} 个结束节点",
            "node_ids": [n["id"] for n in end_nodes],
            "edge_ids": [],
        })

    # 3. Reachability from start
    if len(start_nodes) == 1:
        reachable = _bfs(start_nodes[0]["id"], out_edges)
        unreachable = [n for n in nodes if n["id"] not in reachable]
        if unreachable:
            errors.append({
                "type": "error",
                "message": f"{len(unreachable)} 个节点无法从开始节点到达",
                "node_ids": [n["id"] for n in unreachable],
                "edge_ids": [],
            })

    # 4. Cycle detection (topological sort)
    in_degree = {n.get("id"): 0 for n in nodes}
    for e in edges:
        tgt = e.get("target")
        if tgt in in_degree:
            in_degree[tgt] += 1
    topo_queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
    visited_count = 0
    while topo_queue:
        nid = topo_queue.popleft()
        visited_count += 1
        for edge in out_edges.get(nid, []):
            nxt = edge.get("target")
            if nxt in in_degree:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    topo_queue.append(nxt)
    if visited_count < len(nodes):
        cycle_nodes = [nid for nid, deg in in_degree.items() if deg > 0]
        errors.append({
            "type": "error",
            "message": f"流程中存在循环，涉及 {len(cycle_nodes)} 个节点",
            "node_ids": cycle_nodes,
            "edge_ids": [],
        })

    # 5. Start node should not have incoming edges
    if len(start_nodes) == 1:
        start_id = start_nodes[0]["id"]
        if in_edges.get(start_id):
            errors.append({
                "type": "error",
                "message": "开始节点不应有入边",
                "node_ids": [start_id],
                "edge_ids": [e.get("id") for e in in_edges[start_id]],
            })

    # 6. End node should not have outgoing edges
    if len(end_nodes) == 1:
        end_id = end_nodes[0]["id"]
        if out_edges.get(end_id):
            errors.append({
                "type": "error",
                "message": "结束节点不应有出边",
                "node_ids": [end_id],
                "edge_ids": [e.get("id") for e in out_edges[end_id]],
            })

    # 7. Condition nodes should have true/false branches
    for n in nodes:
        ntype = n.get("data", {}).get("nodeType")
        if ntype == "condition":
            outs = out_edges.get(n["id"], [])
            handles = {e.get("sourceHandle") for e in outs}
            if "condition-true" not in handles:
                warnings.append({
                    "type": "warning",
                    "message": f"条件节点\"{n['data'].get('label', '')}\"缺少'是'分支",
                    "node_ids": [n["id"]],
                    "edge_ids": [],
                })
            if "condition-false" not in handles:
                warnings.append({
                    "type": "warning",
                    "message": f"条件节点\"{n['data'].get('label', '')}\"缺少'否'分支",
                    "node_ids": [n["id"]],
                    "edge_ids": [],
                })

    # 8. Business node uniqueness (max one of each type except custom)
    UNIQUE_BUSINESS_TYPES = {"quote", "contract", "procurement", "delivery", "payment", "settlement"}
    business_type_counts: dict[str, list] = {}
    for n in nodes:
        ntype = n.get("data", {}).get("nodeType")
        if ntype in UNIQUE_BUSINESS_TYPES:
            business_type_counts.setdefault(ntype, []).append(n)
    for btype, bnodes in business_type_counts.items():
        if len(bnodes) > 1:
            errors.append({
                "type": "error",
                "message": f"业务节点「{bnodes[0]['data'].get('label', btype)}」重复出现 {len(bnodes)} 次，每种业务节点最多一个",
                "node_ids": [n["id"] for n in bnodes],
                "edge_ids": [],
            })

    # 9. Non-end nodes without outgoing edges
    for n in nodes:
        ntype = n.get("data", {}).get("nodeType")
        if ntype != "end" and not out_edges.get(n["id"]):
            warnings.append({
                "type": "warning",
                "message": f"节点「{n['data'].get('label', '')}」没有出边，流程将在此中断",
                "node_ids": [n["id"]],
                "edge_ids": [],
            })

    # 10. Custom nodes must be renamed from default label
    for n in nodes:
        ntype = n.get("data", {}).get("nodeType")
        label = n.get("data", {}).get("label", "")
        if ntype == "custom" and label in ("自定义", "custom", ""):
            warnings.append({
                "type": "warning",
                "message": f"自定义节点未命名，请为其指定有意义的名称（如「派遣」「验收」）",
                "node_ids": [n["id"]],
                "edge_ids": [],
            })

    valid = len(errors) == 0
    return {"valid": valid, "errors": errors, "warnings": warnings}


def _bfs(start_id: str, adjacency: dict[str, list]) -> set[str]:
    visited = set()
    queue = deque([start_id])
    visited.add(start_id)
    while queue:
        current = queue.popleft()
        for edge in adjacency.get(current, []):
            nxt = edge.get("target")
            if nxt and nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return visited


# ---------------------------------------------------------------------------
# Workflow Service
# ---------------------------------------------------------------------------

class WorkflowService(BaseService[WorkflowTemplate]):
    def __init__(self):
        super().__init__(WorkflowTemplate)

    # -------------------------------------------------------------------
    # Template operations
    # -------------------------------------------------------------------

    async def list_templates(
        self,
        db: AsyncSession,
        *,
        project_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[WorkflowTemplate], int]:
        query = select(WorkflowTemplate)
        if project_type:
            query = query.where(WorkflowTemplate.project_type == project_type)
        if is_active is not None:
            query = query.where(WorkflowTemplate.is_active == is_active)
        query = query.order_by(WorkflowTemplate.updated_at.desc())
        return await self.list_paginated(db, query=query, page=page, size=size)

    async def create_template(
        self,
        db: AsyncSession,
        *,
        name: str,
        description: Optional[str] = None,
        project_type: Optional[str] = None,
        definition: dict,
        created_by: int,
    ) -> WorkflowTemplate:
        template = WorkflowTemplate(
            name=name,
            description=description,
            project_type=project_type,
            definition=definition,
            created_by=created_by,
            version=1,
            is_active=True,
        )
        db.add(template)
        await db.flush()
        return template

    async def update_template(
        self,
        db: AsyncSession,
        template_id: int,
        **kwargs,
    ) -> WorkflowTemplate:
        template = await self.get_by_id(db, template_id)
        for key, value in kwargs.items():
            if value is not None:
                setattr(template, key, value)
        template.version += 1
        await db.flush()
        return template

    # -------------------------------------------------------------------
    # Instance operations
    # -------------------------------------------------------------------

    async def create_instance(
        self,
        db: AsyncSession,
        *,
        template_id: int,
        order_id: Optional[int] = None,
        name: Optional[str] = None,
        started_by: int,
    ) -> WorkflowInstance:
        template = await self.get_by_id(db, template_id)

        # If order is provided, check it exists
        order = None
        if order_id:
            order = (
                await db.execute(select(Order).where(Order.id == order_id))
            ).scalar_one_or_none()
            if not order:
                raise NotFoundError("订单", order_id)

        # Build order context for condition evaluation
        order_context = self._build_order_context(order) if order else {}

        # Initialize node states from template definition
        definition = template.definition or {}
        nodes = definition.get("nodes", [])
        edges = definition.get("edges", [])
        node_states = {}
        first_node_id = None

        for node in nodes:
            node_id = node.get("id", "")
            node_data = node.get("data", {})
            node_type = node_data.get("nodeType") or node_data.get("type", "task")

            status = WorkflowNodeStatus.PENDING.value
            if node_type == "start":
                status = WorkflowNodeStatus.COMPLETED.value
                first_node_id = node_id

            node_states[node_id] = {
                "status": status,
                "label": node_data.get("label", ""),
                "nodeType": node_type,
                "startedAt": None,
                "completedAt": None,
                "assignee": node_data.get("assignee"),
                "config": node_data.get("config", {}),
            }

        # Find first nodes after start and activate them
        current_node_id = None
        if first_node_id:
            next_node_ids = self._get_next_nodes(first_node_id, edges)
            for next_id in next_node_ids:
                if next_id in node_states:
                    node_type = node_states[next_id].get("nodeType", "task")
                    now_str = datetime.now(timezone.utc).isoformat()

                    # Handle condition node — evaluate and route
                    if node_type == "condition":
                        self._activate_condition_node(
                            next_id, node_states, edges, order_context, now_str
                        )
                    # Handle parallel gateway
                    elif node_type == "parallel_gateway":
                        node_states[next_id]["status"] = WorkflowNodeStatus.COMPLETED.value
                        node_states[next_id]["startedAt"] = now_str
                        node_states[next_id]["completedAt"] = now_str
                        # Activate downstream of gateway
                        self._activate_downstream(
                            next_id, node_states, edges, order_context, now_str
                        )
                    else:
                        node_states[next_id]["status"] = WorkflowNodeStatus.RUNNING.value
                        node_states[next_id]["startedAt"] = now_str
                        if current_node_id is None:
                            current_node_id = next_id

        instance = WorkflowInstance(
            template_id=template_id,
            order_id=order_id,
            name=name or template.name,
            status=WorkflowStatus.RUNNING,
            current_node_id=current_node_id,
            node_states=node_states,
            definition_snapshot=definition,
            started_at=datetime.now(timezone.utc),
            started_by=started_by,
        )
        db.add(instance)
        await db.flush()

        # Audit: instance started
        await self._audit(db, instance.id, action="instance_start", new_status="RUNNING",
                          operator_id=started_by, details={"template_id": template_id})

        return instance

    async def get_instance_detail(
        self, db: AsyncSession, instance_id: int
    ) -> dict:
        instance = (
            await db.execute(
                select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
            )
        ).scalar_one_or_none()
        if not instance:
            raise NotFoundError("工作流实例", instance_id)

        template = (
            await db.execute(
                select(WorkflowTemplate).where(
                    WorkflowTemplate.id == instance.template_id
                )
            )
        ).scalar_one_or_none()

        order = None
        if instance.order_id:
            order = (
                await db.execute(
                    select(Order).where(Order.id == instance.order_id)
                )
            ).scalar_one_or_none()

        # Fetch audit logs
        audit_result = await db.execute(
            select(WorkflowAuditLog)
            .where(WorkflowAuditLog.instance_id == instance_id)
            .order_by(WorkflowAuditLog.created_at.desc())
            .limit(100)
        )
        audit_logs = audit_result.scalars().all()

        # Get operator names
        operator_ids = list({log.operator_id for log in audit_logs if log.operator_id})
        operators_map = {}
        if operator_ids:
            users_result = await db.execute(
                select(User).where(User.id.in_(operator_ids))
            )
            operators_map = {u.id: u for u in users_result.scalars().all()}

        return {
            "instance": instance,
            "template": template,
            "order_no": order.order_no if order else None,
            "audit_logs": [
                {
                    "id": log.id,
                    "instance_id": log.instance_id,
                    "node_id": log.node_id,
                    "action": log.action,
                    "old_status": log.old_status,
                    "new_status": log.new_status,
                    "operator_id": log.operator_id,
                    "operator_name": operators_map.get(log.operator_id, None)
                                     and operators_map[log.operator_id].real_name,
                    "details": log.details,
                    "created_at": log.created_at,
                }
                for log in audit_logs
            ],
        }

    async def advance_node(
        self,
        db: AsyncSession,
        instance_id: int,
        node_id: str,
        new_status: str,
        notes: Optional[str] = None,
        operator_id: Optional[int] = None,
    ) -> WorkflowInstance:
        instance = (
            await db.execute(
                select(WorkflowInstance).where(WorkflowInstance.id == instance_id)
            )
        ).scalar_one_or_none()
        if not instance:
            raise NotFoundError("工作流实例", instance_id)

        if instance.status not in (WorkflowStatus.PENDING, WorkflowStatus.RUNNING):
            raise ConflictError("工作流已完成或已取消，无法操作")

        node_states = dict(instance.node_states)
        if node_id not in node_states:
            raise NotFoundError("工作流节点", node_id)

        # Assignee check: if a node has an assignee, only that user can advance it
        # (skipped for system-triggered advances where operator_id comes from hooks)
        node_assignee = node_states[node_id].get("assignee")
        if (
            node_assignee
            and operator_id
            and new_status in (WorkflowNodeStatus.COMPLETED.value, WorkflowNodeStatus.SKIPPED.value)
        ):
            operator = (
                await db.execute(select(User).where(User.id == operator_id))
            ).scalar_one_or_none()
            if operator and operator.real_name != node_assignee:
                raise ForbiddenError(
                    f"该节点指定由「{node_assignee}」处理，当前用户无权操作"
                )

        now = datetime.now(timezone.utc).isoformat()
        old_status = node_states[node_id].get("status")

        # Update the target node
        node_states[node_id]["status"] = new_status
        if new_status == WorkflowNodeStatus.RUNNING.value:
            node_states[node_id]["startedAt"] = now
        elif new_status in (
            WorkflowNodeStatus.COMPLETED.value,
            WorkflowNodeStatus.SKIPPED.value,
        ):
            node_states[node_id]["completedAt"] = now
        if notes:
            node_states[node_id]["notes"] = notes

        # Audit: node state change
        await self._audit(
            db, instance_id, node_id=node_id,
            action="node_advance" if new_status == WorkflowNodeStatus.COMPLETED.value else f"node_{new_status.lower()}",
            old_status=old_status, new_status=new_status,
            operator_id=operator_id,
            details={"notes": notes} if notes else None,
        )

        # Auto-advance: if completed/skipped, find and activate next nodes
        if new_status in (
            WorkflowNodeStatus.COMPLETED.value,
            WorkflowNodeStatus.SKIPPED.value,
        ):
            # Prefer frozen snapshot; fall back to live template for legacy instances
            snapshot = instance.definition_snapshot
            if snapshot:
                edges = snapshot.get("edges", [])
            else:
                template = (
                    await db.execute(
                        select(WorkflowTemplate).where(
                            WorkflowTemplate.id == instance.template_id
                        )
                    )
                ).scalar_one_or_none()
                edges = (template.definition.get("edges", []) if template else [])

            if edges:

                # Build order context for condition evaluation
                order_context = {}
                if instance.order_id:
                    order = (
                        await db.execute(
                            select(Order).where(Order.id == instance.order_id)
                        )
                    ).scalar_one_or_none()
                    if order:
                        order_context = self._build_order_context(order)

                # Get next nodes
                next_node_ids = self._get_next_nodes(node_id, edges)

                for next_id in next_node_ids:
                    if next_id not in node_states:
                        continue

                    next_state = node_states[next_id]
                    next_type = next_state.get("nodeType", "task")

                    # Check if all predecessors are done (join semantics)
                    predecessors = [
                        e.get("source") for e in edges if e.get("target") == next_id
                    ]
                    all_preds_done = all(
                        node_states.get(p, {}).get("status") in (
                            WorkflowNodeStatus.COMPLETED.value,
                            WorkflowNodeStatus.SKIPPED.value,
                        )
                        for p in predecessors
                    )

                    if not all_preds_done:
                        # For parallel gateway join, mark as WAITING
                        if next_type == "parallel_gateway":
                            mode = next_state.get("config", {}).get("mode", "fork")
                            if mode == "join" and next_state["status"] == WorkflowNodeStatus.PENDING.value:
                                next_state["status"] = WorkflowNodeStatus.WAITING.value
                        continue

                    # All predecessors done — activate this node
                    if next_type == "end":
                        next_state["status"] = WorkflowNodeStatus.COMPLETED.value
                        next_state["completedAt"] = now
                        await self._audit(
                            db, instance_id, node_id=next_id,
                            action="node_auto_complete", new_status="COMPLETED",
                            details={"reason": "end_node"},
                        )
                    elif next_type == "condition":
                        # Evaluate condition and route
                        self._activate_condition_node(
                            next_id, node_states, edges, order_context, now
                        )
                        await self._audit(
                            db, instance_id, node_id=next_id,
                            action="condition_evaluate",
                            new_status=node_states[next_id]["status"],
                            details={
                                "expression": next_state.get("config", {}).get("condition", ""),
                                "result": node_states[next_id]["status"] == WorkflowNodeStatus.COMPLETED.value,
                                "context": order_context,
                            },
                        )
                    elif next_type == "parallel_gateway":
                        mode = next_state.get("config", {}).get("mode", "fork")
                        # Auto-complete gateway and activate downstream
                        next_state["status"] = WorkflowNodeStatus.COMPLETED.value
                        next_state["startedAt"] = now
                        next_state["completedAt"] = now
                        await self._audit(
                            db, instance_id, node_id=next_id,
                            action=f"gateway_{mode}", new_status="COMPLETED",
                        )
                        # Recursively activate downstream
                        self._activate_downstream(
                            next_id, node_states, edges, order_context, now
                        )
                    elif next_type == "timer":
                        # Timer starts running — in production, schedule a Celery task
                        next_state["status"] = WorkflowNodeStatus.RUNNING.value
                        next_state["startedAt"] = now
                        config = next_state.get("config", {})
                        hours = config.get("delay_hours", 0)
                        minutes = config.get("delay_minutes", 0)
                        next_state["timer_fires_at"] = now  # placeholder
                        instance.current_node_id = next_id
                        await self._audit(
                            db, instance_id, node_id=next_id,
                            action="timer_start", new_status="RUNNING",
                            details={"delay_hours": hours, "delay_minutes": minutes},
                        )
                    elif next_type == "subprocess":
                        # Subprocess starts — in production, create child instance
                        next_state["status"] = WorkflowNodeStatus.RUNNING.value
                        next_state["startedAt"] = now
                        instance.current_node_id = next_id
                        config = next_state.get("config", {})
                        await self._audit(
                            db, instance_id, node_id=next_id,
                            action="subprocess_start", new_status="RUNNING",
                            details={"template_id": config.get("template_id")},
                        )
                    elif next_state["status"] in (
                        WorkflowNodeStatus.PENDING.value,
                        WorkflowNodeStatus.WAITING.value,
                    ):
                        next_state["status"] = WorkflowNodeStatus.RUNNING.value
                        next_state["startedAt"] = now
                        instance.current_node_id = next_id

        # Check if all nodes are completed
        all_completed = all(
            s.get("status") in (
                WorkflowNodeStatus.COMPLETED.value,
                WorkflowNodeStatus.SKIPPED.value,
            )
            for s in node_states.values()
        )
        if all_completed:
            instance.status = WorkflowStatus.COMPLETED
            instance.completed_at = datetime.now(timezone.utc)
            await self._audit(
                db, instance_id, action="instance_complete",
                old_status="RUNNING", new_status="COMPLETED",
                operator_id=operator_id,
            )

        instance.node_states = node_states
        await db.flush()

        # Fire workflow hooks: action + notification
        if new_status == WorkflowNodeStatus.COMPLETED.value:
            try:
                from app.services.workflow_hooks import on_node_completed, _notify_running_nodes
                await on_node_completed(db, instance, node_id, operator_id)
                await _notify_running_nodes(db, instance)
            except Exception:
                pass

        return instance

    async def list_instances(
        self,
        db: AsyncSession,
        *,
        order_id: Optional[int] = None,
        template_id: Optional[int] = None,
        status: Optional[WorkflowStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[Sequence[WorkflowInstance], int]:
        query = select(WorkflowInstance)
        if order_id:
            query = query.where(WorkflowInstance.order_id == order_id)
        if template_id:
            query = query.where(WorkflowInstance.template_id == template_id)
        if status:
            query = query.where(WorkflowInstance.status == status)
        query = query.order_by(WorkflowInstance.created_at.desc())
        return await self.list_paginated(db, query=query, page=page, size=size)

    async def get_audit_logs(
        self,
        db: AsyncSession,
        instance_id: int,
        page: int = 1,
        size: int = 50,
    ) -> tuple[Sequence[WorkflowAuditLog], int]:
        """Get paginated audit logs for an instance."""
        query = (
            select(WorkflowAuditLog)
            .where(WorkflowAuditLog.instance_id == instance_id)
            .order_by(WorkflowAuditLog.created_at.desc())
        )
        # Count
        from sqlalchemy import func
        count_result = await db.execute(
            select(func.count())
            .select_from(WorkflowAuditLog)
            .where(WorkflowAuditLog.instance_id == instance_id)
        )
        total = count_result.scalar() or 0

        # Paginate
        result = await db.execute(
            query.offset((page - 1) * size).limit(size)
        )
        return result.scalars().all(), total

    # -------------------------------------------------------------------
    # Condition evaluation
    # -------------------------------------------------------------------

    def evaluate_condition(
        self, expression: str, context: dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Evaluate a condition expression against a context.
        Returns (result: bool, error: str | None)
        """
        try:
            result = _safe_eval(expression, context)
            return result, None
        except BusinessError as e:
            return False, str(e)
        except Exception as e:
            return False, f"条件评估异常: {e}"

    # -------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------

    def _build_order_context(self, order: Order) -> dict[str, Any]:
        """Build the variable context from an order for condition evaluation."""
        return {
            "amount": float(order.total_amount) if order.total_amount else 0,
            "project_type": order.project_type or "",
            "status": order.status or "",
            "currency": order.currency or "",
            "customer_name": getattr(order, "customer_name", "") or "",
            "days_elapsed": (
                (datetime.now(timezone.utc) - order.created_at).days
                if order.created_at else 0
            ),
        }

    def _get_next_nodes(
        self, node_id: str, edges: list[dict]
    ) -> list[str]:
        """Get all target node IDs from outgoing edges of a node."""
        return [
            e.get("target") for e in edges
            if e.get("source") == node_id and e.get("target")
        ]

    def _get_next_nodes_by_handle(
        self, node_id: str, edges: list[dict], handle: str
    ) -> list[str]:
        """Get target node IDs from edges with a specific source handle."""
        return [
            e.get("target") for e in edges
            if e.get("source") == node_id
            and e.get("sourceHandle") == handle
            and e.get("target")
        ]

    def _activate_condition_node(
        self,
        node_id: str,
        node_states: dict,
        edges: list[dict],
        order_context: dict,
        now: str,
    ) -> None:
        """
        Evaluate a condition node and route to the appropriate branch.

        If expression evaluates to True → route via 'condition-true' handle.
        If False → route via 'condition-false' handle.
        If no expression → default to True.
        """
        state = node_states[node_id]
        config = state.get("config", {})
        expression = config.get("condition", "")

        # Evaluate
        if expression and expression.strip():
            result, error = self.evaluate_condition(expression, order_context)
        else:
            result = True  # Default to true branch if no expression

        # Mark condition node as completed
        state["status"] = WorkflowNodeStatus.COMPLETED.value
        state["startedAt"] = now
        state["completedAt"] = now
        state["condition_result"] = result

        # Route to the appropriate branch
        if result:
            targets = self._get_next_nodes_by_handle(node_id, edges, "condition-true")
        else:
            targets = self._get_next_nodes_by_handle(node_id, edges, "condition-false")

        # Activate targets
        for target_id in targets:
            if target_id in node_states:
                target_type = node_states[target_id].get("nodeType", "task")
                if target_type == "end":
                    node_states[target_id]["status"] = WorkflowNodeStatus.COMPLETED.value
                    node_states[target_id]["completedAt"] = now
                elif target_type == "condition":
                    self._activate_condition_node(
                        target_id, node_states, edges, order_context, now
                    )
                elif target_type == "parallel_gateway":
                    node_states[target_id]["status"] = WorkflowNodeStatus.COMPLETED.value
                    node_states[target_id]["startedAt"] = now
                    node_states[target_id]["completedAt"] = now
                    self._activate_downstream(
                        target_id, node_states, edges, order_context, now
                    )
                else:
                    node_states[target_id]["status"] = WorkflowNodeStatus.RUNNING.value
                    node_states[target_id]["startedAt"] = now

        # Skip nodes on the other branch
        other_handle = "condition-false" if result else "condition-true"
        skipped_targets = self._get_next_nodes_by_handle(
            node_id, edges, other_handle
        )
        for target_id in skipped_targets:
            if target_id in node_states:
                # Only skip if the node isn't already activated by another path
                if node_states[target_id]["status"] == WorkflowNodeStatus.PENDING.value:
                    node_states[target_id]["status"] = WorkflowNodeStatus.SKIPPED.value
                    node_states[target_id]["completedAt"] = now

    def _activate_downstream(
        self,
        node_id: str,
        node_states: dict,
        edges: list[dict],
        order_context: dict,
        now: str,
    ) -> None:
        """Activate all downstream nodes of a gateway/completed node."""
        next_ids = self._get_next_nodes(node_id, edges)
        for next_id in next_ids:
            if next_id not in node_states:
                continue
            next_state = node_states[next_id]
            if next_state["status"] != WorkflowNodeStatus.PENDING.value:
                continue

            next_type = next_state.get("nodeType", "task")
            if next_type == "end":
                next_state["status"] = WorkflowNodeStatus.COMPLETED.value
                next_state["completedAt"] = now
            elif next_type == "condition":
                self._activate_condition_node(
                    next_id, node_states, edges, order_context, now
                )
            elif next_type == "parallel_gateway":
                # Check if all predecessors are done for join
                mode = next_state.get("config", {}).get("mode", "fork")
                if mode == "join":
                    preds = [e.get("source") for e in edges if e.get("target") == next_id]
                    all_done = all(
                        node_states.get(p, {}).get("status") in (
                            WorkflowNodeStatus.COMPLETED.value,
                            WorkflowNodeStatus.SKIPPED.value,
                        )
                        for p in preds
                    )
                    if not all_done:
                        next_state["status"] = WorkflowNodeStatus.WAITING.value
                        continue
                next_state["status"] = WorkflowNodeStatus.COMPLETED.value
                next_state["startedAt"] = now
                next_state["completedAt"] = now
                self._activate_downstream(
                    next_id, node_states, edges, order_context, now
                )
            else:
                next_state["status"] = WorkflowNodeStatus.RUNNING.value
                next_state["startedAt"] = now

    async def _audit(
        self,
        db: AsyncSession,
        instance_id: int,
        *,
        node_id: Optional[str] = None,
        action: str,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        operator_id: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> None:
        """Create an audit log entry."""
        log = WorkflowAuditLog(
            instance_id=instance_id,
            node_id=node_id,
            action=action,
            old_status=old_status,
            new_status=new_status,
            operator_id=operator_id,
            details=details,
        )
        db.add(log)


# Singleton
workflow_service = WorkflowService()
