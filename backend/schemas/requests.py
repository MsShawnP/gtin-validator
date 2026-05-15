from __future__ import annotations

from pydantic import BaseModel, Field


class ValidateTextRequest(BaseModel):
    gtins: list[str] = Field(..., max_length=10_000)
