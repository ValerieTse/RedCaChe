from __future__ import annotations

from app.services.ai_base import AIProvider, AISummary
from app.services.classifier import classify_text
from app.services.summarizer import (
    extract_key_points,
    extract_products_or_items,
    extract_steps,
    summarize_text,
)


class MockAIProvider(AIProvider):
    """Deterministic local mock for development and tests."""

    def summarize_and_classify(self, post_payload: dict) -> AISummary:
        title = post_payload.get("title") or "Untitled saved post"
        raw_text = post_payload.get("raw_text") or ""
        ocr_text = post_payload.get("ocr_text") or ""
        category, sub_category = classify_text(title, raw_text, ocr_text)
        key_points = extract_key_points(raw_text or ocr_text)
        products_or_items = extract_products_or_items(raw_text)
        step_by_step = extract_steps(raw_text)
        tags = self._tags_for(category, title, raw_text)

        return AISummary(
            ai_summary=summarize_text(title, raw_text or ocr_text),
            category=category,
            sub_category=sub_category,
            key_points=key_points,
            step_by_step=step_by_step,
            products_or_items=products_or_items,
            useful_for=self._useful_for(category, title),
            tags=tags,
        )

    def _tags_for(self, category: str, title: str, raw_text: str) -> list[str]:
        text = f"{title} {raw_text}".lower()
        tags = [category.lower()]
        for keyword in [
            "routine",
            "checklist",
            "capsule",
            "spf",
            "meeting",
            "study",
            "mobility",
            "home",
            "budget",
            "template",
        ]:
            if keyword in text and keyword not in tags:
                tags.append(keyword)
        return tags[:6]

    def _useful_for(self, category: str, title: str) -> str:
        return f"Finding saved {category.lower()} references related to {title.lower()}."
