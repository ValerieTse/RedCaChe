from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Post, ReviewStatus
from app.time import utc_now


def _frontmatter(title: str, tags: list[str]) -> str:
    tag_lines = "\n".join(f"  - {tag}" for tag in tags)
    return f"---\ntitle: {title}\ntags:\n{tag_lines}\ncreated: {utc_now().isoformat()}\n---\n\n"


def _post_to_markdown(post: Post, include_notes: bool = True) -> str:
    lines = [
        f"## {post.title}",
        "",
        f"- Category: {post.category}",
        f"- Source: {post.source_url}",
    ]
    if post.ai_summary:
        lines.extend(["", "### Summary", post.ai_summary])
    if post.key_points_json:
        lines.extend(["", "### Key Points"])
        lines.extend(f"- {point}" for point in post.key_points_json)
    if include_notes and post.my_notes:
        lines.extend(["", "### My Notes", post.my_notes])
    return "\n".join(lines).strip() + "\n"


def export_daily_review(db: Session, output_root: Path) -> tuple[Path, int, int]:
    output_root.mkdir(parents=True, exist_ok=True)
    posts = (
        db.query(Post)
        .filter(Post.review_status.in_([ReviewStatus.UNREVIEWED.value, ReviewStatus.KEEP.value]))
        .order_by(Post.imported_at.desc())
        .limit(25)
        .all()
    )
    today = date.today().isoformat()
    output_path = output_root / f"xhs-daily-review-{today}.md"
    body = [_frontmatter(f"XHS Daily Review {today}", ["xhs", "daily-review"])]
    body.append(f"# XHS Daily Review {today}\n")
    for post in posts:
        body.append(_post_to_markdown(post, include_notes=True))
    output_path.write_text("\n".join(body), encoding="utf-8")
    return output_path, len(posts), 0


def export_evergreen(
    db: Session,
    output_root: Path,
    post_ids: list[int] | None = None,
) -> tuple[Path, int, int]:
    output_root.mkdir(parents=True, exist_ok=True)
    query = db.query(Post).filter(Post.review_status == ReviewStatus.EVERGREEN.value)
    if post_ids:
        query = query.filter(Post.id.in_(post_ids))
    posts = query.order_by(Post.updated_at.desc()).all()
    skipped_count = 0 if post_ids is None else len(set(post_ids)) - len(posts)
    today = date.today().isoformat()
    output_path = output_root / f"xhs-evergreen-{today}.md"
    body = [_frontmatter(f"XHS Evergreen Notes {today}", ["xhs", "evergreen"])]
    body.append(f"# XHS Evergreen Notes {today}\n")
    for post in posts:
        body.append(_post_to_markdown(post, include_notes=True))
    output_path.write_text("\n".join(body), encoding="utf-8")
    return output_path, len(posts), max(skipped_count, 0)
