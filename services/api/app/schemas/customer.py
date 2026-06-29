"""Customer and Vessel Schemas"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class CustomerBase(BaseModel):
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=50)
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VesselBase(BaseModel):
    name: str = Field(..., max_length=200)
    imo_number: Optional[str] = Field(None, max_length=50)
    customer_id: int
    vessel_type: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class VesselCreate(VesselBase):
    pass


class VesselUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    imo_number: Optional[str] = Field(None, max_length=50)
    vessel_type: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None


class VesselResponse(VesselBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerWithVessels(CustomerResponse):
    vessels: List[VesselResponse] = []

