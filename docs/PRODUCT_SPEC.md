# Product Spec

## Goal

RedCache is a local-first review workspace for Xiaohongshu / RedNote saved posts. It helps import saved posts, organize them with AI summaries and categories, support manual review, and export selected knowledge to Obsidian.

## Product Principles

- AI summarizes and organizes content only.
- The user is the only decision-maker.
- Review status is always chosen manually by the user.
- The app must never ask for or store a Xiaohongshu password.
- Browser automation must use a local visible Playwright browser session with a persistent profile.
- The app must not bypass CAPTCHA, anti-bot checks, private API signatures, or platform restrictions.
- The app must not use reverse-engineered private APIs.
- Batch unfavorite requires explicit manual selection and final confirmation.
- Every future unfavorite action must create a local backup first.
- If backup fails, unfavorite must be skipped for that post.
- Obsidian exports stay clean and intentional.

## Intended Workflow

1. Import saved posts from mock data or a visible logged-in browser session.
2. Run AI summarize/classify.
3. Review cards manually in the dashboard.
4. Mark each post as `keep`, `remove_from_xhs`, `evergreen`, or `archived`.
5. Optionally export daily review summaries.
6. Optionally export manually selected evergreen notes.
7. In a future version, explicitly confirm a batch unfavorite list.
8. Before any future unfavorite action, create a local backup for each selected post.
9. Execute only backed-up, user-confirmed unfavorites.
10. Track restore status for backed-up posts.

## Manual Review Statuses

- `unreviewed`: Imported but not decided.
- `keep`: Keep favorited on Xiaohongshu.
- `remove_from_xhs`: Candidate for future user-confirmed unfavorite.
- `evergreen`: Worth preserving as a clean long-term note.
- `archived`: Locally retained but no longer active in review.

## Current Scope

V1 includes mock import data, local SQLite storage, mock AI organization, a manual review dashboard, and Markdown exports.

V2 adds a visible Playwright import path for cards that are visible to the logged-in user. It uses a persistent local profile and stops on login/challenge states.

Unfavorite automation remains intentionally out of scope.
