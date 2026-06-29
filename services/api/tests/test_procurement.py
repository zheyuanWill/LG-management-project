"""Procurement endpoint tests."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.product import Supplier, SupplierType
from app.models.customer import Customer


async def setup_users(db: AsyncSession) -> dict:
    """Create test users for different roles."""
    users = {}
    for username, role in [
        ("owner", UserRole.OWNER),
        ("pm", UserRole.PM),
        ("proc", UserRole.PROC),
        ("fin", UserRole.FIN),
    ]:
        user = User(
            username=username,
            real_name=f"Test {username}",
            email=f"{username}@test.com",
            role=role,
            hashed_password=get_password_hash("password123"),
            is_active=True,
        )
        db.add(user)
        users[username] = user
    await db.commit()
    for u in users.values():
        await db.refresh(u)
    return users


async def login(client: AsyncClient, username: str) -> str:
    resp = await client.post(
        "/api/auth/login",
        json={"username": username, "password": "password123"},
    )
    return resp.json()["access_token"]


async def create_supplier(db: AsyncSession) -> Supplier:
    supplier = Supplier(
        name="Test Supplier",
        code="SUP001",
        type=SupplierType.MANUFACTURER,
        contact_person="Supplier Contact",
        contact_phone="111222",
    )
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@pytest.mark.asyncio
async def test_create_procurement(client: AsyncClient, db_session: AsyncSession):
    """Test creating a procurement."""
    await setup_users(db_session)
    supplier = await create_supplier(db_session)
    token = await login(client, "proc")

    response = await client.post(
        "/api/procurements",
        json={
            "supplier_id": supplier.id,
            "currency": "CNY",
            "line_items": [
                {
                    "product_name": "Spare Part A",
                    "unit": "件",
                    "quantity": 10,
                    "unit_price": 50.0,
                }
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["procurement_no"].startswith("PO")
    assert data["status"] == "DRAFT"
    assert float(data["total_amount"]) == 500.0


@pytest.mark.asyncio
async def test_procurement_approval_flow(client: AsyncClient, db_session: AsyncSession):
    """Test the full procurement approval workflow."""
    await setup_users(db_session)
    supplier = await create_supplier(db_session)

    proc_token = await login(client, "proc")
    owner_token = await login(client, "owner")

    # Create
    create_resp = await client.post(
        "/api/procurements",
        json={
            "supplier_id": supplier.id,
            "currency": "CNY",
            "line_items": [
                {"product_name": "Part B", "unit": "件", "quantity": 5, "unit_price": 200.0}
            ],
        },
        headers={"Authorization": f"Bearer {proc_token}"},
    )
    proc_id = create_resp.json()["id"]

    # Submit for approval
    submit_resp = await client.post(
        f"/api/procurements/{proc_id}/submit",
        headers={"Authorization": f"Bearer {proc_token}"},
    )
    assert submit_resp.json()["status"] == "PENDING_APPROVAL"

    # Approve
    approve_resp = await client.post(
        f"/api/procurements/{proc_id}/approve",
        json={"approved": True},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert approve_resp.json()["status"] == "APPROVED"

    # Mark ordered
    order_resp = await client.post(
        f"/api/procurements/{proc_id}/order",
        headers={"Authorization": f"Bearer {proc_token}"},
    )
    assert order_resp.json()["status"] == "ORDERED"


@pytest.mark.asyncio
async def test_procurement_rbac(client: AsyncClient, db_session: AsyncSession):
    """Test that only authorized roles can approve procurements."""
    await setup_users(db_session)
    supplier = await create_supplier(db_session)

    proc_token = await login(client, "proc")
    fin_token = await login(client, "fin")

    # Create and submit
    create_resp = await client.post(
        "/api/procurements",
        json={
            "supplier_id": supplier.id,
            "currency": "CNY",
            "line_items": [
                {"product_name": "Part C", "unit": "件", "quantity": 1, "unit_price": 100.0}
            ],
        },
        headers={"Authorization": f"Bearer {proc_token}"},
    )
    proc_id = create_resp.json()["id"]

    await client.post(
        f"/api/procurements/{proc_id}/submit",
        headers={"Authorization": f"Bearer {proc_token}"},
    )

    # FIN should not be able to approve
    resp = await client.post(
        f"/api/procurements/{proc_id}/approve",
        json={"approved": True},
        headers={"Authorization": f"Bearer {fin_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_disbursement_rbac(client: AsyncClient, db_session: AsyncSession):
    """Test that only FIN/OWNER can record disbursements."""
    await setup_users(db_session)
    supplier = await create_supplier(db_session)

    proc_token = await login(client, "proc")

    # PROC should not be able to create disbursement
    create_resp = await client.post(
        "/api/procurements",
        json={
            "supplier_id": supplier.id,
            "currency": "CNY",
            "line_items": [
                {"product_name": "Part D", "unit": "件", "quantity": 1, "unit_price": 100.0}
            ],
        },
        headers={"Authorization": f"Bearer {proc_token}"},
    )
    proc_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/procurements/{proc_id}/disbursements",
        json={
            "supplier_id": supplier.id,
            "amount": 100.0,
            "currency": "CNY",
            "amount_cny": 100.0,
            "payment_date": "2026-02-13",
            "payment_method": "bank_transfer",
        },
        headers={"Authorization": f"Bearer {proc_token}"},
    )
    assert resp.status_code == 403
