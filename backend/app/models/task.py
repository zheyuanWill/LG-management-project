import enum
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class TaskStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    planned_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    project: Mapped["Project"] = relationship(back_populates="tasks")
    daily_updates: Mapped[list["TaskDailyUpdate"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, name={self.name})>"


class TaskDailyUpdate(Base):
    __tablename__ = "task_daily_updates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False, index=True)
    update_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="daily_updates")
    photos: Mapped[list["TaskPhoto"]] = relationship(back_populates="update", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TaskDailyUpdate(id={self.id}, task_id={self.task_id}, date={self.update_date})>"


class TaskPhoto(Base):
    __tablename__ = "task_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    update_id: Mapped[int] = mapped_column(ForeignKey("task_daily_updates.id"), nullable=False, index=True)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    update: Mapped["TaskDailyUpdate"] = relationship(back_populates="photos")

    def __repr__(self) -> str:
        return f"<TaskPhoto(id={self.id}, update_id={self.update_id})>"