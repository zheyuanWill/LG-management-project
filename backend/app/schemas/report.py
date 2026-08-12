from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DailyReportCreate(BaseModel):
    report_date: date
    completed_items: dict | None = None
    tomorrow_plan: str | None = None
    risk_alert: str | None = None


class DailyReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    report_date: date
    # Persisted JSON may be a dict or list depending on earlier writes; accept both.
    completed_items: Any | None = None
    tomorrow_plan: str | None = None
    risk_alert: str | None = None
    confirmed: bool
    created_at: datetime


class DailyReportConfirmRequest(BaseModel):
    confirmed: bool = True


class WeeklyReportCreate(BaseModel):
    week_start_date: date
    week_end_date: date
    summary: str | None = None
    next_week_plan: str | None = None


class WeeklyReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    week_start_date: date
    week_end_date: date
    summary: str | None = None
    next_week_plan: str | None = None
    confirmed: bool
    confirmed_by: int | None = None
    created_at: datetime


class RiskEventCreate(BaseModel):
    title: str = Field(..., max_length=256)
    detail: str | None = None
    risk_level: str = "info"


class RiskEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    title: str
    detail: str | None = None
    risk_level: str
    resolved: bool
    created_at: datetime


class RiskDetectionResponse(BaseModel):
    risk_title: str
    risk_level: str
    suggestion: str
    related_data: dict | None = None