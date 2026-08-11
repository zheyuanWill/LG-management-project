import enum
from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ProjectType(str, enum.Enum):
    SUPERVISION = "supervision"
    BROKERAGE_SALE = "brokerage_sale"
    BROKERAGE_REPAIR = "brokerage_repair"
    SPARE_PARTS = "spare_parts"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    ship_name: Mapped[str] = mapped_column(String(128), nullable=False)
    imo: Mapped[str | None] = mapped_column(String(16), nullable=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    planned_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_completion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    owner: Mapped["Customer | None"] = relationship(back_populates="projects")
    tasks: Mapped[list["Task"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    daily_reports: Mapped[list["DailyReport"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    weekly_reports: Mapped[list["WeeklyReport"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    risk_events: Mapped[list["RiskEvent"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    completion: Mapped["ProjectCompletion | None"] = relationship(back_populates="project", uselist=False)
    brokerage_survey: Mapped["BrokerageSurvey | None"] = relationship(back_populates="project", uselist=False)
    brokerage_commercial: Mapped["BrokerageCommercial | None"] = relationship(back_populates="project", uselist=False)
    brokerage_contract: Mapped["BrokerageContract | None"] = relationship(back_populates="project", uselist=False)
    repair_brokerage: Mapped["RepairBrokerage | None"] = relationship(back_populates="project", uselist=False)
    spare_part_detail: Mapped["SparePartDetail | None"] = relationship(back_populates="project", uselist=False)
    spare_part_photos: Mapped[list["SparePartPhoto"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    logistics_nodes: Mapped[list["LogisticsNode"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    hk_signature: Mapped["HkSignature | None"] = relationship(back_populates="project", uselist=False)
    invoice: Mapped["Invoice | None"] = relationship(back_populates="project", uselist=False)
    quick_saves: Mapped[list["QuickSave"]] = relationship(
        back_populates="project",
        foreign_keys="QuickSave.suggested_project_id",
    )
    files: Mapped[list["File"]] = relationship(back_populates="project")

    __table_args__ = (
        CheckConstraint("type IN ('supervision', 'brokerage_sale', 'brokerage_repair', 'spare_parts')"),
        CheckConstraint("status IN ('active', 'completed', 'cancelled')"),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, project_no={self.project_no})>"


from app.models.customer import Customer
from app.models.report import DailyReport, WeeklyReport, RiskEvent, ProjectCompletion
from app.models.task import Task
from app.models.brokerage import (
    BrokerageSurvey,
    BrokerageCommercial,
    BrokerageContract,
    RepairBrokerage,
)
from app.models.spare_part import (
    SparePartDetail,
    SparePartPhoto,
    LogisticsNode,
    HkSignature,
    Invoice,
)
from app.models.quick_save import QuickSave
from app.models.file import File