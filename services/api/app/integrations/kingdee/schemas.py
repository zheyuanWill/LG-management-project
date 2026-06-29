"""
Pydantic schemas for Kingdee Jingdouyun cloud accounting (jdyaccouting) API.

Field names match the official API exactly — see Postman collection for reference.
"""
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Accounting voucher (云会计凭证)
# POST /jdyaccouting/voucher?mode=1
# Body is a JSON **array** of VoucherCreate objects.
# ---------------------------------------------------------------------------

DC_DEBIT = 1
DC_CREDIT = -1


class VoucherEntry(BaseModel):
    """凭证分录行"""
    acctNo: str = Field(..., description="科目编码, e.g. '1002'")
    dc: int = Field(..., description="借贷方向: 1=借(debit), -1=贷(credit)")
    exp: str = Field("", description="摘要")
    currency: str = Field("RMB", description="币别")
    rate: Decimal = Field(Decimal("1"), description="汇率")
    amount: Decimal = Field(..., description="金额")
    itemClsName: str = Field("", description="辅助核算类别名称")
    itemNo: str = Field("", description="辅助核算编码")
    custNo: str = Field("", description="客户编码")
    suppNo: str = Field("", description="供应商编码")
    deptNo: str = Field("", description="部门编码")
    empNo: str = Field("", description="员工编码")
    inventoryNo: str = Field("", description="存货编码")
    projectNo: str = Field("", description="项目编码")
    qty: Decimal = Field(Decimal("0"), description="数量")
    unit: str = Field("", description="计量单位")
    price: Decimal = Field(Decimal("0"), description="单价")


class VoucherCreate(BaseModel):
    """
    会计凭证 — 提交到 POST /jdyaccouting/voucher 的单个凭证对象。

    注意：API body 是 [VoucherCreate, ...] 数组。
    """
    linkId: str = Field("", description="外部关联ID (幂等去重)")
    groupName: str = Field("记", description="凭证字 (记/收/付/转)")
    vchNumber: int = Field(0, description="凭证号, 0=自动编号")
    date: str = Field(..., description="凭证日期 YYYY-MM-DD")
    yearPeriod: int = Field(..., description="会计期间 YYYYMM, e.g. 202603")
    entries: list[VoucherEntry] = Field(default_factory=list)
