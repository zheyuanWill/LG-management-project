from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SparePartDetail(Base):
    __tablename__ = "spare_part_details"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, unique=True, index=True)
    item_name: Mapped[str] = mapped_column(String(256), nullable=False)
    model_or_drawing: Mapped[str | None] = mapped_column(String(256), nullable=True)
    quantity: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="spare_part_detail")

    def __repr__(self) -> str:
        return f"<SparePartDetail(id={self.id}, project_id={self.project_id})>"


class SparePartPhoto(Base):
    __tablename__ = "spare_part_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    photo_type: Mapped[str] = mapped_column(String(32), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="spare_part_photos")

    def __repr__(self) -> str:
        return f"<SparePartPhoto(id={self.id}, project_id={self.project_id})>"


class LogisticsNode(Base):
    __tablename__ = "logistics_nodes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String(32), nullable=False)
    node_date: Mapped[date] = mapped_column(Date, nullable=False)
    tracking_no: Mapped[str | None] = mapped_column(String(128), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="logistics_nodes")

    def __repr__(self) -> str:
        return f"<LogisticsNode(id={self.id}, project_id={self.project_id}, type={self.node_type})>"


class HkSignature(Base):
    __tablename__ = "hk_signatures"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, unique=True, index=True)
    signature_file_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    signed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="hk_signature")

    def __repr__(self) -> str:
        return f"<HkSignature(id={self.id}, project_id={self.project_id})>"


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, unique=True, index=True)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    tax_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    purpose: Mapped[str] = mapped_column(String(256), nullable=False, default="用于出口退税")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="invoice")

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, project_id={self.project_id})>"