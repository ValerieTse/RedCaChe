# Roadmap

## V1: Mock Import, AI Summary, Dashboard, Obsidian Export

- FastAPI backend.
- SQLite schema.
- Mock sample importer.
- Mock AI summary and classifier.
- Manual review dashboard.
- Daily review export.
- Evergreen Markdown export.

## V2: Playwright Visible Browser Import

- Status: partially implemented.
- Local visible Playwright browser.
- Persistent profile.
- Manual login by the user.
- Import visible saved/favorites cards without private APIs or challenge bypass.
- Selector hints are configurable and may need adjustment as page markup changes.

## V3: Daily Scheduled Import

- Local scheduled import.
- Duplicate detection by `note_id`.
- Change tracking by `last_seen_at`.
- Import summaries for newly discovered saved posts.

## V4: Confirmed Batch Unfavorite With Pre-Unfavorite Backup

- Manual `remove_from_xhs` queue.
- Exact-list confirmation.
- Per-post backup before action.
- Skip action if backup fails.
- Operation logging.

## V5: Restore Workflow

- Restore status tracking.
- Restore instructions from local backup.
- Manual restore support.
- Clear unavailable-state handling.
