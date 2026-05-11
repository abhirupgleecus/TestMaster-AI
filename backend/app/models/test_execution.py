import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.test_report import TestReport
    from app.models.test_script import TestScript


class TestExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestExecution(Base):
    __tablename__ = "test_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    script_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_scripts.id", ondelete="CASCADE"),
        nullable=False,
    )

    status: Mapped[TestExecutionStatus] = mapped_column(
        SqlEnum(
            TestExecutionStatus,
            name="test_execution_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        default=TestExecutionStatus.QUEUED,
    )

    playwright_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    playwright_html_path: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    total_tests: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    passed_tests: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    failed_tests: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    skipped_tests: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    error_log: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    stdout: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    test_script: Mapped["TestScript"] = relationship(
        back_populates="test_executions",
        lazy="selectin",
    )

    test_report: Mapped["TestReport | None"] = relationship(
        back_populates="test_execution",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )
    