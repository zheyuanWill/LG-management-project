"""Order endpoint tests."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.order import Order, OrderStatus, ProjectType


async def create_owner(db: AsyncSession) -> tuple[User, str]:
    """Create an owner user and return (user, token_placeholder)."""
    user = User(
        username="owner",
        real_name="Owner",
        email="owner@test.com",
        role=UserRole.OWNER,
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, "owner"


async def create_pm(db: AsyncSession) -> tuple[User, str]:
    """Create a PM user."""
    user = User(
        username="pm",
        real_name="PM User",
        email="pm@test.com",
        role=UserRole.PM,
        hashed_password=get_password_hash("password123"),
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, "pm"


async def login(client: AsyncClient, username: str) -> str:
    """Login and return access token."""
    response = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "password123"},
    )
    return response.json()["access_token"]


async def create_customer(db: AsyncSession) -> Customer:
    """Create a test customer."""
    customer = Customer(
        name="Test Customer",
        code="CUST001",
        contact_person="John",
        contact_phone="123456",
    )
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@pytest.mark.asyncio
async def test_create_order(client: AsyncClient, db_session: AsyncSession):
    """Test order creation."""
    await create_owner(db_session)
    customer = await create_customer(db_session)
    token = await login(client, "owner")

    response = await client.post(
        "/api/orders",
        json={
            "customer_id": customer.id,
            "project_type": "TECHNICAL_SERVICE",
            "currency": "CNY",
            "line_items": [
                {
                    "product_name": "Test Product",
                    "unit": "件",
                    "quantity": 10,
                    "unit_price": 100.0,
                }
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["order_no"].startswith("ORD")
    assert data["status"] == "DRAFT"
    assert float(data["total_amount"]) == 1000.0


@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient, db_session: AsyncSession):
    """Test order listing with pagination."""
    await create_owner(db_session)
    customer = await create_customer(db_session)
    token = await login(client, "owner")

    # Create a few orders
    for i in range(3):
        await client.post(
            "/api/orders",
            json={
                "customer_id": customer.id,
                "project_type": "TECHNICAL_SERVICE",
                "currency": "CNY",
                "line_items": [
                    {"product_name": f"Product {i}", "unit": "件", "quantity": 1, "unit_price": 100.0}
                ],
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get(
        "/api/orders",
        params={"page": 1, "size": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_get_order_detail(client: AsyncClient, db_session: AsyncSession):
    """Test getting order details."""
    await create_owner(db_session)
    customer = await create_customer(db_session)
    token = await login(client, "owner")

    create_response = await client.post(
        "/api/orders",
        json={
            "customer_id": customer.id,
            "project_type": "TECHNICAL_SERVICE",
            "currency": "CNY",
            "line_items": [
                {"product_name": "Test", "unit": "件", "quantity": 5, "unit_price": 200.0}
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = create_response.json()["id"]

    response = await client.get(
        f"/api/orders/{order_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == order_id
    assert len(data["line_items"]) == 1
    assert data["customer_name"] == "Test Customer"


@pytest.mark.asyncio
async def test_update_order_status(client: AsyncClient, db_session: AsyncSession):
    """Test order status transitions."""
    await create_owner(db_session)
    customer = await create_customer(db_session)
    token = await login(client, "owner")

    # Create order
    create_response = await client.post(
        "/api/orders",
        json={
            "customer_id": customer.id,
            "project_type": "TECHNICAL_SERVICE",
            "currency": "CNY",
            "line_items": [
                {"product_name": "Test", "unit": "件", "quantity": 1, "unit_price": 100.0}
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = create_response.json()["id"]

    # Valid transition: DRAFT -> IN_PROGRESS
    response = await client.put(
        f"/api/orders/{order_id}/status",
        json={"status": "IN_PROGRESS"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"

    # Valid transition: IN_PROGRESS -> COMPLETED
    response = await client.put(
        f"/api/orders/{order_id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_invalid_status_transition(client: AsyncClient, db_session: AsyncSession):
    """Test that invalid status transitions are rejected."""
    await create_owner(db_session)
    customer = await create_customer(db_session)
    token = await login(client, "owner")

    create_response = await client.post(
        "/api/orders",
        json={
            "customer_id": customer.id,
            "project_type": "TECHNICAL_SERVICE",
            "currency": "CNY",
            "line_items": [
                {"product_name": "Test", "unit": "件", "quantity": 1, "unit_price": 100.0}
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = create_response.json()["id"]

    # Invalid: DRAFT -> COMPLETED (must go through IN_PROGRESS)
    response = await client.put(
        f"/api/orders/{order_id}/status",
        json={"status": "COMPLETED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409  # ConflictError / InvalidStateTransitionError


@pytest.mark.asyncio
async def test_order_not_found(client: AsyncClient, db_session: AsyncSession):
    """Test 404 for non-existent order."""
    await create_owner(db_session)
    token = await login(client, "owner")

    response = await client.get(
        "/api/orders/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pm_role_filter(client: AsyncClient, db_session: AsyncSession):
    """Test that PM users only see their own orders."""
    owner_user, _ = await create_owner(db_session)
    pm_user, _ = await create_pm(db_session)
    customer = await create_customer(db_session)

    owner_token = await login(client, "owner")
    pm_token = await login(client, "pm")

    # Owner creates an order (pm_id = owner)
    await client.post(
        "/api/orders",
        json={
            "customer_id": customer.id,
            "project_type": "TECHNICAL_SERVICE",
            "currency": "CNY",
            "line_items": [
                {"product_name": "Owner Order", "unit": "件", "quantity": 1, "unit_price": 100.0}
            ],
        },
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    # PM creates an order (pm_id = pm)
    await client.post(
        "/api/orders",
        json={
            "customer_id": customer.id,
            "project_type": "TECHNICAL_SERVICE",
            "currency": "CNY",
            "line_items": [
                {"product_name": "PM Order", "unit": "件", "quantity": 1, "unit_price": 100.0}
            ],
        },
        headers={"Authorization": f"Bearer {pm_token}"},
    )

    # Owner sees all orders
    owner_response = await client.get(
        "/api/orders",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_response.json()["total"] == 2

    # PM only sees their own
    pm_response = await client.get(
        "/api/orders",
        headers={"Authorization": f"Bearer {pm_token}"},
    )
    assert pm_response.json()["total"] == 1
