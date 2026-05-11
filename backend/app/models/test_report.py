import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SqlEnum, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.test_execution import TestExecution


class TestReportStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"


class TestReport(Base):
    __tablename__ = "test_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("test_executions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    executive_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    detailed_analysis: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    overall_status: Mapped[TestReportStatus] = mapped_column(
        SqlEnum(
            TestReportStatus,
            name="test_report_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        default=TestReportStatus.PARTIAL,
    )

    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    test_execution: Mapped["TestExecution"] = relationship(
        back_populates="test_report",
        lazy="selectin",
    )