from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class QuickSave(Base):
    __tablename__ = "quick_saves"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    recognized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    suggested_project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    confirmed_project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project | None"] = relationship(
        foreign_keys=[suggested_project_id],
        back_populates="quick_saves",
    )

    def __repr__(self) -> str:
        return f"<QuickSave(id={self.id}, type={self.content_type})>"