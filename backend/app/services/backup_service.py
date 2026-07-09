from __future__ import annotations

import json
from pathlib import Path

from app.models import BackupStatus, Post
from app.time import utc_now


def backup_post_to_json(post: Post, backup_root: Path) -> Path:
    backup_root.mkdir(parents=True, exist_ok=True)
    output_path = backup_root / "raw_html" / f"{post.note_id}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "note_id": post.note_id,
        "source_url": post.source_url,
        "title": post.title,
        "author": post.author,
        "raw_text": post.raw_text,
        "ocr_text": post.ocr_text,
        "ai_summary": post.ai_summary,
        "created_at": utc_now().isoformat(),
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    post.backup_status = BackupStatus.RAW_SAVED.value
    post.operation_logs_json = [
        *post.operation_logs_json,
        {
            "event": "backup_created",
            "path": str(output_path),
            "created_at": utc_now().isoformat(),
        },
    ]
    return output_path
