import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.test_case import TestCase
    from app.models.test_script import TestScript


class GenerationSessionStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    AWAITING_SELECTION = "awaiting_selection"
    SCRIPT_GENERATED = "script_generated"
    EXECUTED = "executed"
    REPORTED = "reported"


class GenerationSession(Base):
    __tablename__ = "generation_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    context_input: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[GenerationSessionStatus] = mapped_column(
        SqlEnum(
            GenerationSessionStatus,
            name="generation_session_status",
            values_callable=lambda enum: [e.value for e in enum],
        ),
        nullable=False,
        default=GenerationSessionStatus.PENDING,
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

    project: Mapped["Project"] = relationship(
        back_populates="generation_sessions",
        lazy="selectin",
    )

    test_cases: Mapped[list["TestCase"]] = relationship(
        back_populates="generation_session",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TestCase.order_index",
    )

    test_script: Mapped["TestScript | None"] = relationship(
        back_populates="generation_session",
        cascade="all, delete-orphan",
        lazy="selectin",
        uselist=False,
    )