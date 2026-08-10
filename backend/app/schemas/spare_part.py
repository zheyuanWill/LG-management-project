from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class SparePartDetailCreate(BaseModel):
    item_name: str = Field(..., max_length=256)
    model_or_drawing: str | None = Field(default=None, max_length=256)
    quantity: str | None = Field(default=None, max_length=64)


class SparePartDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    item_name: str
    model_or_drawing: str | None = None
    quantity: str | None = None
    created_at: datetime


class SparePartPhotoCreate(BaseModel):
    photo_type: str = Field(..., max_length=32)
    storage_key: str = Field(..., max_length=512)


class SparePartPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    photo_type: str
    storage_key: str
    created_at: datetime


class LogisticsNodeCreate(BaseModel):
    node_type: str = Field(..., max_length=32)
    node_date: date
    tracking_no: str | None = Field(default=None, max_length=128)
    remark: str | None = None
    attachment_key: str | None = Field(default=None, max_length=512)


class LogisticsNodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    node_type: str
    node_date: date
    tracking_no: str | None = None
    remark: str | None = None
    attachment_key: str | None = None
    created_at: datetime


class HkSignatureCreate(BaseModel):
    signature_file_key: str | None = Field(default=None, max_length=512)
    signed_at: date | None = None


class HkSignatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    signature_file_key: str | None = None
    signed_at: date | None = None
    created_at: datetime


class InvoiceCreate(BaseModel):
    title: str | None = Field(default=None, max_length=256)
    tax_number: str | None = Field(default=None, max_length=64)
    amount: float | None = None
    purpose: str = Field(default="用于出口退税", max_length=256)


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str | None = None
    tax_number: str | None = None
    amount: float | None = None
    purpose: str
    created_at: datetime