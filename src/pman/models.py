"""Modelli database SQLAlchemy per SMOT-PMANAGER."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TaskStatus(StrEnum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class TaskSource(StrEnum):
    GITHUB = "github"
    VAULT = "vault"
    CODE = "code"
    AI = "ai"
    MANUAL = "manual"


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(
        String(20), default=ProjectStatus.ACTIVE
    )
    last_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    health_score: Mapped[float | None] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    tasks: Mapped[list[Task]] = relationship(back_populates="project")
    reports: Mapped[list[Report]] = relationship(back_populates="project")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[TaskSource] = mapped_column(String(20), default=TaskSource.MANUAL)
    status: Mapped[TaskStatus] = mapped_column(String(20), default=TaskStatus.BACKLOG)
    priority: Mapped[int] = mapped_column(Integer, default=3)
    complexity: Mapped[int | None] = mapped_column(Integer)  # story points
    assigned_to: Mapped[str | None] = mapped_column(String(100))
    labels: Mapped[str | None] = mapped_column(Text)  # JSON array
    file_path: Mapped[str | None] = mapped_column(Text)
    line_start: Mapped[int | None] = mapped_column(Integer)
    ai_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project] = relationship(back_populates="tasks")


class Sprint(Base):
    __tablename__ = "sprints"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    goal: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="planned")
    velocity: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("projects.id"))
    content: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    ai_model: Mapped[str | None] = mapped_column(String(100))

    project: Mapped[Project] = relationship(back_populates="reports")


class WBSTask(Base):
    __tablename__ = "wbs_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    parent_id: Mapped[str | None] = mapped_column(String(50))
    duration_days: Mapped[int | None] = mapped_column(Integer)
    dependencies: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="planned")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="open")
    description: Mapped[str | None] = mapped_column(Text)
    resolution: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Risk(Base):
    __tablename__ = "risks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    probability: Mapped[str] = mapped_column(String(20), default="medium")
    impact: Mapped[str] = mapped_column(String(20), default="medium")
    mitigation: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="identified")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
