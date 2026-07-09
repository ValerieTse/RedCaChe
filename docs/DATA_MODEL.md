# Data Model

## Post

The `posts` table is the local source of truth.

| Field | Purpose |
| --- | --- |
| `id` | Local primary key |
| `note_id` | Xiaohongshu note identifier or imported stable identifier |
| `source_url` | Original note URL |
| `import_source` | `mock` or `xiaohongshu` |
| `import_run_id` | Import run that last imported or saw the post |
| `thumbnail_url` | Best-effort visible thumbnail URL |
| `raw_payload_json` | Raw importer payload for local debugging |
| `title` | Saved post title |
| `author` | Author display name |
| `author_url` | Author profile URL |
| `collected_date` | Date the item was collected, when known |
| `imported_at` | Local import timestamp |
| `last_seen_at` | Last time importer saw the note |
| `raw_text` | Imported text body |
| `ocr_text` | OCR text from screenshots, when available |
| `ai_summary` | AI-generated summary |
| `category` | One allowed category |
| `sub_category` | AI-generated subcategory label |
| `key_points_json` | JSON list of key points |
| `step_by_step_json` | JSON list of steps |
| `products_or_items_json` | JSON list of mentioned products/items |
| `useful_for` | AI-generated retrieval context |
| `tags_json` | JSON list of tags |
| `my_notes` | User notes |
| `review_status` | Manual review decision |
| `xhs_favorite_status` | Xiaohongshu favorite state |
| `backup_status` | Local backup state |
| `restore_status` | Restore workflow state |
| `unfavorite_status` | Future batch unfavorite state |
| `screenshot_paths_json` | JSON list of local screenshot paths |
| `operation_logs_json` | JSON list of local operation events |
| `created_at` | Local row creation timestamp |
| `updated_at` | Local row update timestamp |

## ImportRun

The `import_runs` table records visible import attempts.

| Field | Purpose |
| --- | --- |
| `import_run_id` | Stable run identifier |
| `started_at` | Run start timestamp |
| `finished_at` | Run completion timestamp |
| `status` | `running`, `completed`, `stopped`, or `failed` |
| `scanned_count` | Visible cards scanned |
| `imported_count` | New posts imported |
| `duplicate_count` | Duplicate cards or existing records skipped |
| `failed_count` | Records that failed to save |
| `stopped_reason` | Safe-stop reason, if any |
| `error_message` | Error details, if any |

## Import Source

- `mock`
- `xiaohongshu`
- `rednote`

## Allowed Categories

- Beauty
- Fashion
- Fitness
- Work
- Study
- Life
- Food
- Travel
- Other

## Review Status

- `unreviewed`
- `keep`
- `remove_from_xhs`
- `evergreen`
- `archived`

## Favorite Status

- `favorited`
- `unfavorited`
- `unknown`
- `restored`

## Backup Status

- `raw_saved`
- `snapshot_saved`
- `full_backup_saved`
- `backup_failed`

## Restore Status

- `not_needed`
- `restorable`
- `restored`
- `unavailable`

## Unfavorite Status

- `not_requested`
- `queued`
- `processing`
- `unfavorited`
- `failed`
- `skipped`
