from __future__ import annotations

import re


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？.!?])\s+|[\n\r]+", text.strip())
    return [part.strip(" 。！？.!?") for part in parts if part.strip()]


def summarize_text(title: str, raw_text: str | None, max_sentences: int = 3) -> str:
    title = title or "未命名收藏"
    source = (raw_text or "").strip()
    if len(source) < 20 or source == title:
        return f"这条保存内容目前只有卡片级信息：{title}。需要详情页富集后才能生成更完整的摘要。"

    sentences = _sentences(source)
    if not sentences:
        return f"这条笔记围绕「{title}」提供参考，但当前可见正文较少。建议运行详情富集以补全内容。"

    selected: list[str] = []
    seen: set[str] = set()
    for sentence in sentences:
        cleaned = re.sub(r"\s+", " ", sentence).strip()
        if len(cleaned) < 8 or cleaned in seen:
            continue
        seen.add(cleaned)
        selected.append(cleaned)
        if len(selected) >= max_sentences:
            break

    if not selected:
        return f"这条笔记围绕「{title}」提供参考，但当前可见正文较少。建议运行详情富集以补全内容。"

    if len(selected) == 1:
        summary = f"这条笔记围绕「{title}」展开，核心内容是：{selected[0]}。"
    else:
        summary = f"这条笔记围绕「{title}」整理了可复用信息。{selected[0]}。{selected[1]}。"
        if len(selected) >= 3:
            summary += f"{selected[2]}。"
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
