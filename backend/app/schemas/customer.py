from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    name: str = Field(..., max_length=256)
    contact_person: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    survey_conclusion: str | None = Field(default=None, max_length=20)
    remarks: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=256)
    contact_person: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    survey_conclusion: str | None = Field(default=None, max_length=20)
    remarks: str | None = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    contact_person: str | None = None
    phone: str | None = None
    survey_conclusion: str | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int