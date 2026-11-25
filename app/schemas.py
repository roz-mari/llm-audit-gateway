from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


class AskResponse(BaseModel):
    answer: str
    tools_used: list[str]
    redactions: list[str]


class LogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    answer: str | None
    tools_used: list[str]
    redactions: list[str]
    total_tokens: int
    latency_ms: int
    status: str
    created_at: datetime
