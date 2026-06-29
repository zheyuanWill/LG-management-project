"""Analytics & voucher sync tests.

Tests cover:
1. All GET /analytics/* endpoints return valid responses
2. Voucher auto-sync hooks fire on business events (mocked Kingdee client)
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from unittest.mock import AsyncMock, patch, MagicMock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.customer import Customer
from app.models.order import Order, OrderStatus, ProjectType, Currency
from app.models.contract import Contract, ContractStatus, PaymentRecord
from app.models.procurement import Procurement, ProcurementStatus, Disbursement
from app.models.settlement import Settlement, SettlementStatus, CostItem, CostCategory
from app.models.product import Supplier


async def _seed(db: AsyncSession):
    """Seed minimal data for analytics tests."""
    owner = User(
        username="owner", real_name="Owner", email="o@t.com",
        role=UserRole.OWNER, hashed_password=get_password_hash("password123"), is_active=True,
    )
    fin = User(
        username="fin", real_name="Finance", email="f@t.com",
        role=UserRole.FIN, hashed_password=get_password_hash("password123"), is_active=True,
    )
    db.add_all([owner, fin])
    await db.flush()

    cust = Customer(name="TestCust", code="C001")
    db.add(cust)
    await db.flush()

    supplier = Supplier(name="TestSupp", code="S001", type="GOODS")
    db.add(supplier)
    await db.flush()

    order = Order(
        order_no="ORD-TEST-001", customer_id=cust.id, project_type=ProjectType.SPARE_PARTS,
        status=OrderStatus.IN_PROGRESS, currency=Currency.CNY, total_amount=Decimal("100000"),
        pm_id=owner.id,
    )
    db.add(order)
    await db.flush()

    cat = CostCategory(name="材料费", code="MAT")
    db.add(cat)
    await db.flush()

    settlement = Settlement(
        settlement_no="STL-TEST-001", order_id=order.id,
        status=SettlementStatus.APPROVED,
        total_revenue=Decimal("100000"), total_revenue_cny=Decimal("100000"),
        total_cost=Decimal("60000"), total_cost_cny=Decimal("60000"),
        gross_profit=Decimal("40000"), gross_profit_rate=Decimal("40"),
        applicant_id=owner.id, apply_date=date.today(),
        approver_id=owner.id, approve_date=date.today(),
    )
    db.add(settlement)
    await db.flush()

    cost_item = CostItem(
        settlement_id=settlement.id, order_id=order.id, category_id=cat.id,
        description="钢材", amount=Decimal("60000"), amount_cny=Decimal("60000"),
    )
    db.add(cost_item)

    contract = Contract(
        contract_no="CON-TEST-001", order_id=order.id, customer_id=cust.id,
        title="Test Contract", status=ContractStatus.EXECUTING,
        total_amount=Decimal("100000"),
    )
    db.add(contract)
    await db.flush()

    payment = PaymentRecord(
        contract_id=contract.id, order_id=order.id,
        amount=Decimal("50000"), amount_cny=Decimal("50000"),
        payment_date=date.today(),
    )
    db.add(payment)

    procurement = Procurement(
        procurement_no="PO-TEST-001", supplier_id=supplier.id, order_id=order.id,
        status=ProcurementStatus.APPROVED, total_amount=Decimal("30000"),
        created_by=owner.id,
    )
    db.add(procurement)
    await db.flush()

    disbursement = Disbursement(
        procurement_id=procurement.id, order_id=order.id, supplier_id=supplier.id,
        amount=Decimal("15000"), amount_cny=Decimal("15000"),
        payment_date=date.today(),
    )
    db.add(disbursement)
    await db.commit()
    return owner, cust, order, settlement, contract, procurement, supplier


async def _login(client: AsyncClient, username: str = "owner") -> str:
    r = await client.post("/api/auth/login", json={"username": username, "password": "password123"})
    return r.json()["access_token"]


# ─── Analytics GET endpoints ─────────────────────────────────────

@pytest.mark.asyncio
async def test_profitability(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    token = await _login(client)
    r = await client.get("/api/analytics/profitability?months=3", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 3
    assert "revenue" in data[0]
    assert "cost" in data[0]
    assert "profit" in data[0]
    assert "margin" in data[0]


@pytest.mark.asyncio
async def test_ar_ap(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    token = await _login(client)
    r = await client.get("/api/analytics/ar-ap", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "accounts_receivable" in data
    assert "accounts_payable" in data
    assert data["contract_total"] == 100000.0
    assert data["received_total"] == 50000.0
    assert data["accounts_receivable"] == 50000.0
    assert data["procurement_total"] == 30000.0
    assert data["disbursed_total"] == 15000.0
    assert data["accounts_payable"] == 15000.0


@pytest.mark.asyncio
async def test_revenue_by_customer(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    token = await _login(client)
    r = await client.get("/api/analytics/revenue-by-customer?top=5", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["customer"] == "TestCust"
    assert data[0]["revenue"] == 100000.0


@pytest.mark.asyncio
async def test_revenue_by_project_type(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    token = await _login(client)
    r = await client.get("/api/analytics/revenue-by-project-type", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["label"] == "备件供应"


@pytest.mark.asyncio
async def test_cost_breakdown(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    token = await _login(client)
    r = await client.get("/api/analytics/cost-breakdown", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["category"] == "材料费"
    assert data[0]["total"] == 60000.0


@pytest.mark.asyncio
async def test_cashflow(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    token = await _login(client)
    r = await client.get("/api/analytics/cashflow?months=3", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    has_current = any(d.get("received", 0) > 0 or d.get("disbursed", 0) > 0 for d in data)
    assert has_current


@pytest.mark.asyncio
async def test_project_profitability(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    token = await _login(client)
    r = await client.get("/api/analytics/project-profitability", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert "rows" in data
    assert "summary" in data
    assert len(data["rows"]) == 1
    row = data["rows"][0]
    assert row["order_no"] == "ORD-TEST-001"
    assert row["revenue"] == 100000.0
    assert row["cost"] == 60000.0
    assert row["profit"] == 40000.0
    assert row["margin"] == 40.0
    assert row["received"] == 50000.0
    assert row["disbursed"] == 15000.0
    assert data["summary"]["total_revenue"] == 100000.0


@pytest.mark.asyncio
async def test_sync_logs_empty(client: AsyncClient, db_session: AsyncSession):
    await _seed(db_session)
    token = await _login(client)
    r = await client.get("/api/analytics/sync-logs", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0


# ─── Voucher auto-sync hooks (mocked Kingdee) ───────────────────

@pytest.mark.asyncio
async def test_settlement_approve_triggers_sync(client: AsyncClient, db_session: AsyncSession):
    """Approving a settlement should trigger Kingdee voucher sync."""
    entities = await _seed(db_session)
    owner = entities[0]
    settlement = entities[3]

    settlement.status = SettlementStatus.PENDING_APPROVAL
    await db_session.commit()

    token = await _login(client)

    mock_resp = {"code": 0, "msg": "成功", "list": [{"vchId": 123, "vchNo": 1, "code": 0}]}
    with patch("app.integrations.kingdee.sync_service.KingdeeSyncService") as MockSvc:
        mock_instance = MagicMock()
        mock_instance.sync_settlement = AsyncMock(return_value=MagicMock(status="success"))
        MockSvc.return_value = mock_instance

        r = await client.post(
            f"/api/settlements/{settlement.id}/approve",
            json={"approved": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        mock_instance.sync_settlement.assert_called_once()


@pytest.mark.asyncio
async def test_disbursement_create_triggers_sync(client: AsyncClient, db_session: AsyncSession):
    """Creating a disbursement should trigger Kingdee voucher sync."""
    entities = await _seed(db_session)
    procurement = entities[5]
    supplier = entities[6]
    order = entities[2]

    token = await _login(client)

    with patch("app.integrations.kingdee.sync_service.KingdeeSyncService") as MockSvc:
        mock_instance = MagicMock()
        mock_instance.sync_disbursement = AsyncMock(return_value=MagicMock(status="success"))
        MockSvc.return_value = mock_instance

        r = await client.post(
            f"/api/procurements/{procurement.id}/disbursements",
            json={
                "supplier_id": supplier.id,
                "order_id": order.id,
                "amount": 5000,
                "currency": "CNY",
                "amount_cny": 5000,
                "payment_date": "2026-03-15",
                "payment_method": "银行转账",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        mock_instance.sync_disbursement.assert_called_once()
