from __future__ import annotations

from app.services.ai_base import AIProvider, AISummary
from app.services.classifier import classify_text


class MockAIProvider(AIProvider):
    """Deterministic local mock for development and tests."""

    def summarize_and_classify(self, post_payload: dict) -> AISummary:
        title = post_payload.get("title") or "Untitled saved post"
        category, sub_category = classify_text(title)

        return AISummary(
            ai_summary=None,
            category=category,
            sub_category=sub_category,
            key_points=[],
            step_by_step=[],
            products_or_items=[],
            useful_for=None,
            tags=[],
        )
