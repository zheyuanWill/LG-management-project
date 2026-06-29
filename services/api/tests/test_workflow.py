"""Workflow endpoint tests."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User, UserRole


async def create_user_and_login(
    db: AsyncSession,
    client: AsyncClient,
    username: str = "owner",
    role: UserRole = UserRole.OWNER,
) -> str:
    """Create user and return access token."""
    user = User(
        username=username,
        real_name=f"Test {username}",
        email=f"{username}@test.com",
        role=role,
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db.add(user)
    await db.commit()

    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "password123"},
    )
    return response.json()["access_token"]


SAMPLE_DEFINITION = {
    "nodes": [
        {"id": "start_1", "type": "custom", "position": {"x": 0, "y": 100}, "data": {"label": "开始", "nodeType": "start"}},
        {"id": "task_1", "type": "custom", "position": {"x": 300, "y": 100}, "data": {"label": "需求确认", "nodeType": "task", "days": 3}},
        {"id": "approval_1", "type": "custom", "position": {"x": 600, "y": 100}, "data": {"label": "方案审批", "nodeType": "approval", "days": 2}},
        {"id": "end_1", "type": "custom", "position": {"x": 900, "y": 100}, "data": {"label": "结束", "nodeType": "end"}},
    ],
    "edges": [
        {"id": "e_start_task", "source": "start_1", "target": "task_1"},
        {"id": "e_task_approval", "source": "task_1", "target": "approval_1"},
        {"id": "e_approval_end", "source": "approval_1", "target": "end_1"},
    ],
}


@pytest.mark.asyncio
async def test_create_template(client: AsyncClient, db_session: AsyncSession):
    """Test creating a workflow template."""
    token = await create_user_and_login(db_session, client)

    response = await client.post(
        "/api/workflows/templates",
        json={
            "name": "技术服务标准流程",
            "description": "标准技术服务项目工作流",
            "project_type": "TECHNICAL_SERVICE",
            "definition": SAMPLE_DEFINITION,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "技术服务标准流程"
    assert data["version"] == 1
    assert len(data["definition"]["nodes"]) == 4
    assert len(data["definition"]["edges"]) == 3


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient, db_session: AsyncSession):
    """Test listing workflow templates."""
    token = await create_user_and_login(db_session, client)

    # Create two templates
    for i in range(2):
        await client.post(
            "/api/workflows/templates",
            json={
                "name": f"Template {i}",
                "project_type": "TECHNICAL_SERVICE",
                "definition": SAMPLE_DEFINITION,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get(
        "/api/workflows/templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    # Check list response has node/edge counts
    assert data["items"][0]["node_count"] == 4
    assert data["items"][0]["edge_count"] == 3


@pytest.mark.asyncio
async def test_get_template(client: AsyncClient, db_session: AsyncSession):
    """Test getting template detail with full definition."""
    token = await create_user_and_login(db_session, client)

    create_resp = await client.post(
        "/api/workflows/templates",
        json={"name": "Test", "definition": SAMPLE_DEFINITION},
        headers={"Authorization": f"Bearer {token}"},
    )
    template_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/workflows/templates/{template_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == template_id
    assert "definition" in data
    assert len(data["definition"]["nodes"]) == 4


@pytest.mark.asyncio
async def test_update_template(client: AsyncClient, db_session: AsyncSession):
    """Test updating a template increments version."""
    token = await create_user_and_login(db_session, client)

    create_resp = await client.post(
        "/api/workflows/templates",
        json={"name": "Original", "definition": SAMPLE_DEFINITION},
        headers={"Authorization": f"Bearer {token}"},
    )
    template_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/workflows/templates/{template_id}",
        json={"name": "Updated Name"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["version"] == 2  # Version incremented


@pytest.mark.asyncio
async def test_delete_template(client: AsyncClient, db_session: AsyncSession):
    """Test deleting a template."""
    token = await create_user_and_login(db_session, client)

    create_resp = await client.post(
        "/api/workflows/templates",
        json={"name": "ToDelete", "definition": SAMPLE_DEFINITION},
        headers={"Authorization": f"Bearer {token}"},
    )
    template_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/workflows/templates/{template_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Verify deleted
    get_resp = await client.get(
        f"/api/workflows/templates/{template_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_instance(client: AsyncClient, db_session: AsyncSession):
    """Test creating a workflow instance from a template."""
    token = await create_user_and_login(db_session, client)

    # Create template
    create_resp = await client.post(
        "/api/workflows/templates",
        json={"name": "Flow", "definition": SAMPLE_DEFINITION},
        headers={"Authorization": f"Bearer {token}"},
    )
    template_id = create_resp.json()["id"]

    # Create instance
    response = await client.post(
        "/api/workflows/instances",
        json={"template_id": template_id, "name": "Test Instance"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RUNNING"
    assert data["template_id"] == template_id
    # Start node should be completed, first task should be running
    assert data["node_states"]["start_1"]["status"] == "COMPLETED"
    assert data["node_states"]["task_1"]["status"] == "RUNNING"


@pytest.mark.asyncio
async def test_advance_node(client: AsyncClient, db_session: AsyncSession):
    """Test advancing workflow nodes."""
    token = await create_user_and_login(db_session, client)

    # Create template + instance
    tpl_resp = await client.post(
        "/api/workflows/templates",
        json={"name": "Flow", "definition": SAMPLE_DEFINITION},
        headers={"Authorization": f"Bearer {token}"},
    )
    inst_resp = await client.post(
        "/api/workflows/instances",
        json={"template_id": tpl_resp.json()["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    instance_id = inst_resp.json()["id"]

    # Advance task_1 to COMPLETED
    response = await client.put(
        f"/api/workflows/instances/{instance_id}/advance",
        json={"node_id": "task_1", "status": "COMPLETED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["node_states"]["task_1"]["status"] == "COMPLETED"
    assert data["node_states"]["approval_1"]["status"] == "RUNNING"

    # Advance approval_1 to COMPLETED
    response = await client.put(
        f"/api/workflows/instances/{instance_id}/advance",
        json={"node_id": "approval_1", "status": "COMPLETED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    # End node should auto-complete, workflow should be COMPLETED
    assert data["node_states"]["end_1"]["status"] == "COMPLETED"
    assert data["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_get_instance_detail(client: AsyncClient, db_session: AsyncSession):
    """Test getting instance detail includes full definition."""
    token = await create_user_and_login(db_session, client)

    tpl_resp = await client.post(
        "/api/workflows/templates",
        json={"name": "Flow", "definition": SAMPLE_DEFINITION},
        headers={"Authorization": f"Bearer {token}"},
    )
    inst_resp = await client.post(
        "/api/workflows/instances",
        json={"template_id": tpl_resp.json()["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    instance_id = inst_resp.json()["id"]

    response = await client.get(
        f"/api/workflows/instances/{instance_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "definition" in data
    assert len(data["definition"]["nodes"]) == 4
