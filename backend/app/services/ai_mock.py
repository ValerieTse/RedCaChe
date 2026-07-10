from __future__ import annotations

from app.services.ai_base import AIProvider, AISummary
from app.services.classifier import classify_title


class MockAIProvider(AIProvider):
    """Deterministic local mock for development and tests.

    ``category_defs`` (``[{name, keywords}]``) scopes classification to the user's
    active categories. When omitted, every built-in preset is considered.
    """

    def __init__(self, category_defs: list[dict] | None = None) -> None:
        self.category_defs = category_defs

    def summarize_and_classify(self, post_payload: dict) -> AISummary:
        title = post_payload.get("title") or "Untitled saved post"
        category = classify_title(title, self.category_defs)

        return AISummary(
            ai_summary=None,
            category=category,
            sub_category=None,
            key_points=[],
            step_by_step=[],
            products_or_items=[],
            useful_for=None,
            tags=[],
        )
