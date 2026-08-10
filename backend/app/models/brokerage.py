from datetime import datetime

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class BrokerageSurvey(Base):
    __tablename__ = "brokerage_surveys"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, unique=True, index=True)
    conclusion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    survey_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="brokerage_survey")

    def __repr__(self) -> str:
        return f"<BrokerageSurvey(id={self.id}, project_id={self.project_id})>"


class BrokerageCommercial(Base):
    __tablename__ = "brokerage_commercials"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, unique=True, index=True)
    quote_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    commission_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unpaid")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="brokerage_commercial")

    def __repr__(self) -> str:
        return f"<BrokerageCommercial(id={self.id}, project_id={self.project_id})>"


class BrokerageContract(Base):
    __tablename__ = "brokerage_contracts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, unique=True, index=True)
    moa_file_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="brokerage_contract")

    def __repr__(self) -> str:
        return f"<BrokerageContract(id={self.id}, project_id={self.project_id})>"


class RepairBrokerage(Base):
    __tablename__ = "repair_brokerages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, unique=True, index=True)
    shipyard_quote: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    contract_file_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    handed_over: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    handed_over_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="repair_brokerage")

    def __repr__(self) -> str:
        return f"<RepairBrokerage(id={self.id}, project_id={self.project_id})>"