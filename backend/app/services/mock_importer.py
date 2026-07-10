from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import ImportSource, Post, ReviewStatus, XhsFavoriteStatus
from app.services.ai_base import AIProvider
from app.services.ai_mock import MockAIProvider
from app.time import utc_now


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def import_sample_posts(
    db: Session,
    sample_path: Path,
    ai_provider: AIProvider | None = None,
) -> tuple[int, int]:
    provider = ai_provider or MockAIProvider()
    payloads = json.loads(sample_path.read_text(encoding="utf-8"))
    imported_count = 0
    updated_count = 0
    now = utc_now()

    for payload in payloads:
        ai = provider.summarize_and_classify(payload)
        post = db.query(Post).filter(Post.note_id == payload["note_id"]).one_or_none()
        if post is None:
            post = Post(
                note_id=payload["note_id"],
                source_url=payload["source_url"],
                import_source=ImportSource.MOCK.value,
                raw_payload_json=payload,
                title=payload["title"],
                author=payload.get("author"),
                author_url=payload.get("author_url"),
                collected_date=_parse_date(payload.get("collected_date")),
                imported_at=now,
                last_seen_at=now,
                raw_text=payload.get("raw_text"),
                ocr_text=payload.get("ocr_text"),
                ai_summary=ai.ai_summary,
                category=ai.category,
                sub_category=ai.sub_category,
                key_points_json=ai.key_points,
                step_by_step_json=ai.step_by_step,
                products_or_items_json=ai.products_or_items,
                useful_for=ai.useful_for,
                tags_json=ai.tags,
                review_status=ReviewStatus.UNREVIEWED.value,
                xhs_favorite_status=XhsFavoriteStatus.FAVORITED.value,
                created_at=now,
                updated_at=now,
            )
            db.add(post)
            imported_count += 1
        else:
            post.source_url = payload["source_url"]
            post.import_source = post.import_source or ImportSource.MOCK.value
            post.raw_payload_json = payload
            post.title = payload["title"]
            post.author = payload.get("author")
            post.author_url = payload.get("author_url")
            post.collected_date = _parse_date(payload.get("collected_date"))
            post.last_seen_at = now
            post.raw_text = payload.get("raw_text")
            post.ocr_text = payload.get("ocr_text")
            post.ai_summary = ai.ai_summary
            if not post.category_is_manual:
                post.category = ai.category
                post.sub_category = ai.sub_category
            post.key_points_json = ai.key_points
            post.step_by_step_json = ai.step_by_step
            post.products_or_items_json = ai.products_or_items
            post.useful_for = ai.useful_for
            post.tags_json = ai.tags
            post.updated_at = now
            updated_count += 1

    db.commit()
    return imported_count, updated_count
