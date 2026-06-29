"""
Workflow Hooks — Bridges between business entities and workflow engine.

Two directions:
  1. Business → Workflow:  when a business entity status changes,
     auto-advance matching workflow nodes (trigger mechanism).
  2. Workflow → Business:  when a workflow node completes,
     fire the configured business action (action mechanism).

Also handles:
  - Auto-creating workflow instances when orders start.
  - Sending notifications when nodes become RUNNING.
"""
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import (
    WorkflowTemplate,
    WorkflowInstance,
    WorkflowStatus,
    WorkflowNodeStatus,
)
from app.models.notification import NotificationType
from app.models.user import User

logger = logging.getLogger("workflow.hooks")

BUSINESS_NODE_TRIGGERS: dict[str, dict[str, str]] = {
    "quote": {"entity": "quote", "status": "ACCEPTED"},
    "contract": {"entity": "contract", "status": "EFFECTIVE"},
    "procurement": {"entity": "procurement", "status": "APPROVED"},
    "settlement": {"entity": "settlement", "status": "APPROVED"},
}


# ---------------------------------------------------------------------------
# 1. Auto-create workflow instance when an order starts
# ---------------------------------------------------------------------------

async def auto_create_workflow_for_order(
    db: AsyncSession,
    order_id: int,
    project_type: str,
    started_by: int,
) -> Optional[WorkflowInstance]:
    """
    Find an active workflow template matching the order's project_type
    and create an instance automatically.

    Returns the created instance, or None if no matching template.
    """
    from app.services.workflow_service import workflow_service

    result = await db.execute(
        select(WorkflowTemplate)
        .where(
            WorkflowTemplate.is_active == True,
            WorkflowTemplate.project_type == project_type,
        )
        .order_by(WorkflowTemplate.version.desc())
        .limit(1)
    )
    template = result.scalar_one_or_none()

    if not template:
        logger.info(
            "No active workflow template for project_type=%s, skipping auto-create",
            project_type,
        )
        return None

    try:
        instance = await workflow_service.create_instance(
            db,
            template_id=template.id,
            order_id=order_id,
            name=f"{template.name}",
            started_by=started_by,
        )
        logger.info(
            "Auto-created workflow instance %s for order %s (template=%s)",
            instance.id, order_id, template.name,
        )

        await _notify_running_nodes(db, instance)
        return instance
    except Exception as e:
        logger.warning("Failed to auto-create workflow for order %s: %s", order_id, e)
        return None


# ---------------------------------------------------------------------------
# 2. Business status change → auto-advance workflow nodes (trigger)
# ---------------------------------------------------------------------------

async def on_entity_status_change(
    db: AsyncSession,
    entity_type: str,
    entity_id: int,
    new_status: str,
    order_id: Optional[int] = None,
    operator_id: Optional[int] = None,
) -> int:
    """
    When a business entity status changes, find related workflow instances
    and advance nodes whose `config.trigger` matches.

    Trigger config on a node:
        { "trigger": { "entity": "procurement", "status": "APPROVED" } }

    Returns the number of nodes advanced.
    """
    from app.services.workflow_service import workflow_service

    if not order_id:
        return 0

    instances = await _get_running_instances_for_order(db, order_id)
    advanced_count = 0

    for instance in instances:
        node_states = instance.node_states or {}
        for node_id, state in node_states.items():
            if state.get("status") != WorkflowNodeStatus.RUNNING.value:
                continue

            trigger = state.get("config", {}).get("trigger")
            if not trigger:
                node_type = state.get("nodeType", "")
                trigger = BUSINESS_NODE_TRIGGERS.get(node_type)
            if not trigger:
                continue

            if (
                trigger.get("entity") == entity_type
                and trigger.get("status") == new_status
            ):
                try:
                    await workflow_service.advance_node(
                        db,
                        instance.id,
                        node_id=node_id,
                        new_status=WorkflowNodeStatus.COMPLETED.value,
                        notes=f"由{entity_type}#{entity_id}状态变更为{new_status}自动触发",
                        operator_id=operator_id,
                    )
                    advanced_count += 1
                    logger.info(
                        "Auto-advanced node %s in instance %s (trigger: %s.%s)",
                        node_id, instance.id, entity_type, new_status,
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to auto-advance node %s in instance %s: %s",
                        node_id, instance.id, e,
                    )

    if advanced_count > 0:
        for instance in instances:
            await _notify_running_nodes(db, instance)

    return advanced_count


# ---------------------------------------------------------------------------
# 3. Workflow node completed → fire business action (action)
# ---------------------------------------------------------------------------

async def on_node_completed(
    db: AsyncSession,
    instance: WorkflowInstance,
    node_id: str,
    operator_id: Optional[int] = None,
) -> None:
    """
    After a workflow node is completed, check its `config.action`
    and execute the corresponding business operation.

    Action config on a node:
        { "action": { "type": "change_status", "entity": "order", "status": "COMPLETED" } }
        { "action": { "type": "notify", "message": "采购审批已通过" } }
    """
    node_states = instance.node_states or {}
    state = node_states.get(node_id, {})
    action = state.get("config", {}).get("action")

    if not action:
        return

    action_type = action.get("type")

    if action_type == "change_status":
        await _execute_status_change(db, instance, action, operator_id)
    elif action_type == "notify":
        await _execute_notify(db, instance, action)
    else:
        logger.warning("Unknown action type: %s on node %s", action_type, node_id)


async def _execute_status_change(
    db: AsyncSession,
    instance: WorkflowInstance,
    action: dict,
    operator_id: Optional[int],
) -> None:
    """Execute a change_status action from workflow node config."""
    entity = action.get("entity")
    new_status = action.get("status")

    if not entity or not new_status:
        return

    try:
        if entity == "order" and instance.order_id:
            from app.services.order_service import order_service
            from app.models.order import OrderStatus
            await order_service.update_status(
                db, instance.order_id, OrderStatus(new_status)
            )
            logger.info(
                "Workflow action: order %s status → %s",
                instance.order_id, new_status,
            )
    except Exception as e:
        logger.warning("Workflow action failed (change_status %s → %s): %s", entity, new_status, e)


async def _execute_notify(
    db: AsyncSession,
    instance: WorkflowInstance,
    action: dict,
) -> None:
    """Execute a notify action from workflow node config."""
    message = action.get("message", "工作流通知")

    if instance.started_by:
        from app.routers.notification import create_notification
        await create_notification(
            db,
            user_id=instance.started_by,
            type=NotificationType.INFO,
            title=message,
            content=f"工作流「{instance.name}」通知: {message}",
            related_type="workflow",
            related_id=instance.id,
        )


# ---------------------------------------------------------------------------
# 4. Notification helpers
# ---------------------------------------------------------------------------

async def _notify_running_nodes(
    db: AsyncSession,
    instance: WorkflowInstance,
) -> None:
    """
    For all RUNNING nodes with an assignee, send a notification
    to the assignee user.
    """
    from app.routers.notification import create_notification

    node_states = instance.node_states or {}

    for node_id, state in node_states.items():
        if state.get("status") != WorkflowNodeStatus.RUNNING.value:
            continue

        assignee_name = state.get("assignee")
        if not assignee_name:
            continue

        user = await _find_user_by_name(db, assignee_name)
        if not user:
            continue

        try:
            await create_notification(
                db,
                user_id=user.id,
                type=NotificationType.APPROVAL,
                title=f"待处理: {state.get('label', node_id)}",
                content=f"工作流「{instance.name}」的节点「{state.get('label', node_id)}」需要您处理",
                related_type="workflow",
                related_id=instance.id,
            )
        except Exception as e:
            logger.warning("Failed to notify user %s for node %s: %s", assignee_name, node_id, e)


async def _find_user_by_name(db: AsyncSession, name: str) -> Optional[User]:
    """Look up a user by real_name (for assignee matching)."""
    result = await db.execute(
        select(User).where(User.real_name == name, User.is_active == True).limit(1)
    )
    return result.scalar_one_or_none()


async def _get_running_instances_for_order(
    db: AsyncSession,
    order_id: int,
) -> list[WorkflowInstance]:
    """Get all RUNNING workflow instances for an order."""
    result = await db.execute(
        select(WorkflowInstance).where(
            WorkflowInstance.order_id == order_id,
            WorkflowInstance.status == WorkflowStatus.RUNNING,
        )
    )
    return list(result.scalars().all())
