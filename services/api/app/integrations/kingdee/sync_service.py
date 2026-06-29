"""
Kingdee Sync Service — pushes accounting vouchers to Kingdee Cloud Accounting.

Only the jdyaccouting (云会计) API is used. Master data (customers, suppliers,
products) and SCM documents (sale orders, purchase instocks) are managed
entirely within LG and are NOT synced to Kingdee.

All sync operations:
1. Build the mapped voucher payload via mapper
2. Write a SyncLog(status=PENDING)
3. POST to /jdyaccouting/voucher
4. Update SyncLog to SUCCESS or FAILED
"""
import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.sync_log import SyncLog, SyncDirection, SyncStatus
from app.models.customer import Customer
from app.models.product import Supplier
from app.models.order import Order
from app.models.procurement import Procurement, Disbursement
from app.models.settlement import Settlement
from app.models.contract import PaymentRecord

from app.integrations.kingdee.client import KingdeeClient, KingdeeAPIError, get_kingdee_client
from app.integrations.kingdee import mapper

logger = logging.getLogger("kingdee.sync")

VOUCHER_API_PATH = "/jdyaccouting/voucher"


class KingdeeSyncService:
    """Stateless service — receives client and db from caller."""

    def __init__(self, client: Optional[KingdeeClient] = None):
        self.client = client or get_kingdee_client()

    # ------------------------------------------------------------------
    # Order -> Sale voucher (借:应收  贷:收入; 借:成本  贷:库存)
    # ------------------------------------------------------------------

    async def sync_order(self, db: AsyncSession, order_id: int) -> SyncLog:
        result = await db.execute(
            select(Order).options(selectinload(Order.line_items)).where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        if not order:
            return await self._skip_log(db, "order", order_id, "voucher", "订单不存在")

        customer = (await db.execute(
            select(Customer).where(Customer.id == order.customer_id)
        )).scalar_one_or_none()
        if not customer:
            return await self._skip_log(db, "order", order_id, "voucher", "客户不存在")

        revenue = sum(li.amount for li in order.line_items)
        cost = Decimal("0")
        payload = mapper.map_sale_voucher(order, customer, revenue, cost)

        return await self._execute(
            db,
            entity_type="order",
            entity_id=order_id,
            kingdee_doc_type="voucher",
            api_path=VOUCHER_API_PATH,
            payload=payload.model_dump(),
        )

    # ------------------------------------------------------------------
    # Procurement received -> Purchase voucher (借:库存商品  贷:应付账款)
    # ------------------------------------------------------------------

    async def sync_procurement_received(self, db: AsyncSession, procurement_id: int) -> SyncLog:
        result = await db.execute(
            select(Procurement)
            .options(selectinload(Procurement.line_items))
            .where(Procurement.id == procurement_id)
        )
        procurement = result.scalar_one_or_none()
        if not procurement:
            return await self._skip_log(db, "procurement", procurement_id, "voucher", "采购单不存在")

        supplier = (await db.execute(
            select(Supplier).where(Supplier.id == procurement.supplier_id)
        )).scalar_one_or_none()
        if not supplier:
            return await self._skip_log(db, "procurement", procurement_id, "voucher", "供应商不存在")

        total = sum(
            (li.received_quantity or li.quantity) * li.unit_price
            for li in procurement.line_items
        )
        payload = mapper.map_purchase_instock_voucher(procurement, supplier, total)

        return await self._execute(
            db,
            entity_type="procurement",
            entity_id=procurement_id,
            kingdee_doc_type="voucher",
            api_path=VOUCHER_API_PATH,
            payload=payload.model_dump(),
        )

    # ------------------------------------------------------------------
    # Disbursement -> Payment voucher (借:应付账款  贷:银行存款)
    # ------------------------------------------------------------------

    async def sync_disbursement(self, db: AsyncSession, disbursement_id: int) -> SyncLog:
        disbursement = (await db.execute(
            select(Disbursement).where(Disbursement.id == disbursement_id)
        )).scalar_one_or_none()
        if not disbursement:
            return await self._skip_log(db, "disbursement", disbursement_id, "voucher", "付款记录不存在")

        procurement = (await db.execute(
            select(Procurement).where(Procurement.id == disbursement.procurement_id)
        )).scalar_one_or_none()

        supplier = (await db.execute(
            select(Supplier).where(Supplier.id == disbursement.supplier_id)
        )).scalar_one_or_none()

        if not procurement or not supplier:
            return await self._skip_log(db, "disbursement", disbursement_id, "voucher", "关联数据不存在")

        payload = mapper.map_disbursement_voucher(disbursement, supplier, procurement.procurement_no)
        return await self._execute(
            db,
            entity_type="disbursement",
            entity_id=disbursement_id,
            kingdee_doc_type="voucher",
            api_path=VOUCHER_API_PATH,
            payload=payload.model_dump(),
        )

    # ------------------------------------------------------------------
    # Settlement -> Summary voucher (借:应收  贷:收入; 借:成本  贷:库存)
    # ------------------------------------------------------------------

    async def sync_settlement(self, db: AsyncSession, settlement_id: int) -> SyncLog:
        settlement = (await db.execute(
            select(Settlement).where(Settlement.id == settlement_id)
        )).scalar_one_or_none()
        if not settlement:
            return await self._skip_log(db, "settlement", settlement_id, "voucher", "结算不存在")

        order = (await db.execute(
            select(Order).where(Order.id == settlement.order_id)
        )).scalar_one_or_none()

        customer = None
        if order:
            customer = (await db.execute(
                select(Customer).where(Customer.id == order.customer_id)
            )).scalar_one_or_none()

        if not order or not customer:
            return await self._skip_log(db, "settlement", settlement_id, "voucher", "关联订单/客户不存在")

        revenue = settlement.total_revenue_cny or settlement.total_revenue or Decimal("0")
        cost = settlement.total_cost_cny or settlement.total_cost or Decimal("0")
        payload = mapper.map_sale_voucher(order, customer, revenue, cost)

        return await self._execute(
            db,
            entity_type="settlement",
            entity_id=settlement_id,
            kingdee_doc_type="voucher",
            api_path=VOUCHER_API_PATH,
            payload=payload.model_dump(),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _execute(
        self,
        db: AsyncSession,
        *,
        entity_type: str,
        entity_id: int,
        kingdee_doc_type: str,
        api_path: str,
        payload: dict,
    ) -> SyncLog:
        log = SyncLog(
            entity_type=entity_type,
            entity_id=entity_id,
            kingdee_doc_type=kingdee_doc_type,
            direction=SyncDirection.LG_TO_JDY,
            status=SyncStatus.PENDING,
            request_payload=payload,
        )
        db.add(log)
        await db.flush()

        try:
            # jdyaccouting/voucher expects a JSON array and mode=1 query param
            resp = await self.client.post(
                api_path,
                json=[payload],
                params={"mode": "1"},
            )
            log.response_payload = resp

            # Response: {"msg":"成功","code":0,"list":[{"vchId":...,"vchNo":...,"code":0}]}
            resp_code = resp.get("code")
            items = resp.get("list", [])
            first = items[0] if items else {}
            item_code = first.get("code", -1)

            if resp_code == 0 and item_code == 0:
                log.status = SyncStatus.SUCCESS
                log.kingdee_doc_no = str(first.get("vchId", "")) or str(first.get("vchNo", ""))
            else:
                item_msg = first.get("msg", resp.get("msg", "未知错误"))
                log.status = SyncStatus.FAILED
                log.error_message = f"[{item_code}] {item_msg}"

            logger.info(
                "Sync %s: %s #%d -> %s [%s]",
                log.status.value, entity_type, entity_id, kingdee_doc_type,
                log.kingdee_doc_no or "no doc no",
            )

        except KingdeeAPIError as exc:
            log.status = SyncStatus.FAILED
            log.error_message = f"[{exc.code}] {exc.message}"
            log.response_payload = exc.response
            log.retry_count += 1
            logger.error("Sync FAILED: %s #%d -> %s: %s", entity_type, entity_id, kingdee_doc_type, exc)

        except Exception as exc:
            log.status = SyncStatus.FAILED
            log.error_message = str(exc)
            log.retry_count += 1
            logger.exception("Sync ERROR: %s #%d -> %s", entity_type, entity_id, kingdee_doc_type)

        await db.flush()
        return log

    async def _skip_log(
        self,
        db: AsyncSession,
        entity_type: str,
        entity_id: int,
        doc_type: str,
        reason: str,
    ) -> SyncLog:
        log = SyncLog(
            entity_type=entity_type,
            entity_id=entity_id,
            kingdee_doc_type=doc_type,
            direction=SyncDirection.LG_TO_JDY,
            status=SyncStatus.SKIPPED,
            error_message=reason,
        )
        db.add(log)
        await db.flush()
        return log
