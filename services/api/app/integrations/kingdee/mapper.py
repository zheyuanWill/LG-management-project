"""
Field mapper: LG models -> Kingdee Jingdouyun cloud accounting vouchers.

All mapping logic is centralised here so changes to either side
only need to be updated in one place.
"""
from datetime import date
from decimal import Decimal

from app.models.customer import Customer
from app.models.product import Supplier
from app.models.order import Order
from app.models.procurement import Procurement, Disbursement
from app.models.contract import PaymentRecord
from app.integrations.kingdee.schemas import (
    VoucherCreate,
    VoucherEntry,
    DC_DEBIT,
    DC_CREDIT,
)


# ---------------------------------------------------------------------------
# Configurable account codes — these should match the chart of accounts
# in the customer's Kingdee accounting book.
# Override via environment or admin UI in a future version.
# ---------------------------------------------------------------------------

class AccountCodes:
    INVENTORY = "1405"           # 库存商品
    ACCOUNTS_RECEIVABLE = "1122" # 应收账款
    ACCOUNTS_PAYABLE = "2202"    # 应付账款
    BANK = "1002"                # 银行存款
    REVENUE = "6001"             # 主营业务收入
    COGS = "6401"                # 主营业务成本


# ---------------------------------------------------------------------------
# Voucher mappers
# ---------------------------------------------------------------------------

def _year_period(dt) -> int:
    """Convert a datetime/date to YYYYMM int."""
    if isinstance(dt, str):
        return int(dt[:4]) * 100 + int(dt[5:7])
    if hasattr(dt, "year") and hasattr(dt, "month"):
        return dt.year * 100 + dt.month
    return int(str(dt)[:4]) * 100 + int(str(dt)[5:7])


def _date_str(dt) -> str:
    """Convert a datetime/date to YYYY-MM-DD string."""
    if isinstance(dt, str):
        return dt[:10]
    if hasattr(dt, "strftime"):
        return dt.strftime("%Y-%m-%d")
    return str(dt)[:10]


def _entry(acct: str, dc: int, amount: Decimal, exp: str, **aux) -> VoucherEntry:
    """Build a single voucher entry row."""
    return VoucherEntry(
        acctNo=acct,
        dc=dc,
        exp=exp,
        amount=amount,
        custNo=aux.get("custNo", ""),
        suppNo=aux.get("suppNo", ""),
    )


def map_sale_voucher(
    order: Order,
    customer: Customer,
    revenue: Decimal,
    cost: Decimal,
) -> VoucherCreate:
    """销售 -> 借:应收  贷:收入; 借:成本  贷:库存"""
    cust = customer.code or f"C{customer.id:06d}"
    summary = f"销售确认 {order.order_no}"
    entries = [
        _entry(AccountCodes.ACCOUNTS_RECEIVABLE, DC_DEBIT, revenue, summary, custNo=cust),
        _entry(AccountCodes.REVENUE, DC_CREDIT, revenue, summary),
    ]
    if cost > 0:
        entries += [
            _entry(AccountCodes.COGS, DC_DEBIT, cost, summary),
            _entry(AccountCodes.INVENTORY, DC_CREDIT, cost, summary),
        ]
    return VoucherCreate(
        linkId=f"SO-{order.order_no}",
        groupName="记",
        date=_date_str(order.created_at),
        yearPeriod=_year_period(order.created_at),
        entries=entries,
    )


def map_purchase_instock_voucher(
    procurement: Procurement,
    supplier: Supplier,
    total_amount: Decimal,
) -> VoucherCreate:
    """采购入库 -> 借:库存商品  贷:应付账款"""
    supp = supplier.code or f"S{supplier.id:06d}"
    summary = f"采购入库 {procurement.procurement_no}"
    return VoucherCreate(
        linkId=f"PI-{procurement.procurement_no}",
        groupName="记",
        date=_date_str(procurement.created_at),
        yearPeriod=_year_period(procurement.created_at),
        entries=[
            _entry(AccountCodes.INVENTORY, DC_DEBIT, total_amount, summary, suppNo=supp),
            _entry(AccountCodes.ACCOUNTS_PAYABLE, DC_CREDIT, total_amount, summary, suppNo=supp),
        ],
    )


def map_disbursement_voucher(
    disbursement: Disbursement,
    supplier: Supplier,
    procurement_no: str,
) -> VoucherCreate:
    """采购付款 -> 借:应付账款  贷:银行存款"""
    supp = supplier.code or f"S{supplier.id:06d}"
    amount = disbursement.amount_cny or disbursement.amount
    summary = f"采购付款 {procurement_no}"
    dt = disbursement.payment_date or disbursement.created_at
    return VoucherCreate(
        linkId=f"PD-{procurement_no}-{disbursement.id}",
        groupName="付",
        date=_date_str(dt),
        yearPeriod=_year_period(dt),
        entries=[
            _entry(AccountCodes.ACCOUNTS_PAYABLE, DC_DEBIT, amount, summary, suppNo=supp),
            _entry(AccountCodes.BANK, DC_CREDIT, amount, summary),
        ],
    )


def map_payment_received_voucher(
    payment: PaymentRecord,
    customer: Customer,
) -> VoucherCreate:
    """收到回款 -> 借:银行存款  贷:应收账款"""
    cust = customer.code or f"C{customer.id:06d}"
    amount = payment.amount_cny or payment.amount
    summary = f"回款 订单{payment.order_id}"
    dt = payment.payment_date or payment.created_at
    return VoucherCreate(
        linkId=f"PR-{payment.id}",
        groupName="收",
        date=_date_str(dt),
        yearPeriod=_year_period(dt),
        entries=[
            _entry(AccountCodes.BANK, DC_DEBIT, amount, summary),
            _entry(AccountCodes.ACCOUNTS_RECEIVABLE, DC_CREDIT, amount, summary, custNo=cust),
        ],
    )
