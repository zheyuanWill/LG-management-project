from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BrokerageSurveyCreate(BaseModel):
    conclusion: str | None = Field(default=None, max_length=20)
    survey_detail: str | None = None


class BrokerageSurveyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    conclusion: str | None = None
    survey_detail: str | None = None
    created_at: datetime


class BrokerageCommercialCreate(BaseModel):
    quote_amount: float = 0
    commission_amount: float = 0
    payment_status: str = "unpaid"


class BrokerageCommercialResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    quote_amount: float
    commission_amount: float
    payment_status: str
    created_at: datetime


class BrokerageContractCreate(BaseModel):
    moa_file_key: str | None = Field(default=None, max_length=512)


class BrokerageContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    moa_file_key: str | None = None
    created_at: datetime


class RepairBrokerageCreate(BaseModel):
    shipyard_quote: float = 0
    contract_file_key: str | None = Field(default=None, max_length=512)
    handed_over: bool = False


class RepairBrokerageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    shipyard_quote: float
    contract_file_key: str | None = None
    handed_over: bool
    handed_over_at: datetime | None = None
    created_at: datetime


class ProjectCompletionCreate(BaseModel):
    completion_cert_key: str = Field(..., max_length=512)
    acceptance_cert_key: str = Field(..., max_length=512)


class ProjectCompletionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    completion_cert_key: str
    acceptance_cert_key: str
    completed_at: datetime