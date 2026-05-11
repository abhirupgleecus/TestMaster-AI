import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TestStep(BaseModel):
    step_number: int = Field(
        ge=1,
    )

    action: str = Field(
        min_length=1,
    )

    expected_result: str = Field(
        min_length=1,
    )


class TestCaseCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=500,
    )

    description: str = Field(
        min_length=1,
    )

    preconditions: str | None = None

    steps: list[TestStep] = Field(
        min_length=1,
    )

    expected_output: str = Field(
        min_length=1,
    )

    is_selected: bool = False

    order_index: int = Field(
        ge=0,
    )


class TestCaseResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID

    title: str
    description: str
    preconditions: str | None

    steps: list[TestStep]

    expected_output: str

    is_selected: bool
    order_index: int

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)