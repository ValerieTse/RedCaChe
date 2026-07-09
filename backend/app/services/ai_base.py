from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class AISummary(BaseModel):
    ai_summary: str
    category: str
    sub_category: str | None = None
    key_points: list[str] = Field(default_factory=list)
    step_by_step: list[str] = Field(default_factory=list)
    products_or_items: list[str] = Field(default_factory=list)
    useful_for: str | None = None
    tags: list[str] = Field(default_factory=list)


class AIProvider(ABC):
    @abstractmethod
    def summarize_and_classify(self, post_payload: dict) -> AISummary:
        """Return organization metadata only, never a keep/remove decision."""
