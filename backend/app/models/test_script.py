import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.generation_session import GenerationSession
    from app.models.test_execution import TestExecution


class TestScriptStatus(str, Enum):
    GENERATED = "generated"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class TestScript(Base):
    __tablename__ = "test_scripts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generation_sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    script_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    status: Mapped[TestScriptStatus] = mapped_column(
        SqlEnum(
            TestScriptStatus,
            name="test_script_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        default=TestScriptStatus.GENERATED,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    generation_session: Mapped["GenerationSession"] = relationship(
        back_populates="test_script",
        lazy="selectin",
    )

    test_executions: Mapped[list["TestExecution"]] = relationship(
        back_populates="test_script",
        cascade="all, delete-orphan",
        lazy="selectin",
    )