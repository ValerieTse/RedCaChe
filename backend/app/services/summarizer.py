from __future__ import annotations

import re


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


def summarize_text(title: str, raw_text: str | None, max_sentences: int = 2) -> str:
    source = raw_text or title
    sentences = _sentences(source)
    if not sentences:
        return f"Saved reference about {title}."
    selected = sentences[:max_sentences]
    summary = " ".join(selected)
    if len(summary) > 320:
        summary = summary[:317].rstrip() + "..."
    return summary


def extract_key_points(raw_text: str | None, limit: int = 4) -> list[str]:
    if not raw_text:
        return []

    candidates: list[str] = []
    for line in re.split(r"[\n;]+", raw_text):
        cleaned = re.sub(r"^\s*[-*\d.)]+\s*", "", line).strip()
        if len(cleaned) >= 24:
            candidates.append(cleaned)

    if len(candidates) < limit:
        for sentence in _sentences(raw_text):
            if len(sentence) >= 24 and sentence not in candidates:
                candidates.append(sentence)

    return [point[:180].rstrip() for point in candidates[:limit]]


def extract_steps(raw_text: str | None) -> list[str]:
    if not raw_text:
        return []
    steps = []
    for line in raw_text.splitlines():
        cleaned = line.strip()
        if re.match(r"^(step\s*\d+|\d+[.)])", cleaned.lower()):
            steps.append(re.sub(r"^(step\s*\d+[:.)]?|\d+[.)])\s*", "", cleaned, flags=re.I))
    return steps[:6]


def extract_products_or_items(raw_text: str | None) -> list[str]:
    if not raw_text:
        return []
    items = []
    for marker in ["items:", "products:", "tools:", "uses:"]:
        lower = raw_text.lower()
        index = lower.find(marker)
        if index >= 0:
            segment = raw_text[index + len(marker) :].splitlines()[0]
            items.extend(item.strip(" .") for item in segment.split(",") if item.strip())
    return items[:8]
