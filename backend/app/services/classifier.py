from __future__ import annotations

from app.category_presets import CATEGORY_PRESETS, UNCATEGORIZED_SLUG


# Default keyword definitions covering every built-in preset. Callers that know
# the user's active category selection should pass their own defs instead.
DEFAULT_CATEGORY_DEFS: list[dict] = [
    {"name": preset["slug"], "keywords": tuple(preset["keywords"])}
    for preset in CATEGORY_PRESETS
]


def classify_title(title: str, category_defs: list[dict] | None = None) -> str:
    """Classify from the saved-post title only.

    Body text and OCR are intentionally ignored because they are unavailable or
    unreliable for many video posts. Ties are broken by ``category_defs`` order.
    """
    defs = category_defs if category_defs is not None else DEFAULT_CATEGORY_DEFS
    haystack = (title or "").strip().lower()
    best_category = UNCATEGORIZED_SLUG
    best_score = 0

    for definition in defs:
        keywords = definition.get("keywords") or ()
        score = sum(1 for keyword in keywords if keyword and keyword.lower() in haystack)
        if score > best_score:
            best_score = score
            best_category = definition["name"]

    return best_category


def classify_text(
    title: str,
    raw_text: str | None = None,
    ocr_text: str | None = None,
    category_defs: list[dict] | None = None,
) -> tuple[str, str | None]:
    """Backward-compatible wrapper returning ``(category, sub_category)``."""
    del raw_text, ocr_text
    return classify_title(title, category_defs), None
