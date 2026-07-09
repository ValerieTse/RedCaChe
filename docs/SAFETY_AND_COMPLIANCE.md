# Safety And Compliance

## Non-Negotiables

- No Xiaohongshu password storage.
- No CAPTCHA bypass.
- No anti-bot bypass.
- No private API reverse engineering.
- No private signature generation.
- No AI-driven unfavorite decisions.
- No automatic unfavorite based on summaries, categories, or tags.
- No hidden browser automation.

## Browser Automation Rules

Playwright automation must run in a visible local browser with a persistent profile. The user completes login and any platform challenge manually. Automation must stop when access is blocked, challenged, or ambiguous.

For V2, RedCache only imports visible saved/favorites post cards. It must not click unfavorite controls, mutate Xiaohongshu state, bypass challenges, or call private APIs.

## AI Rules

AI providers may return:

- Summary
- Category
- Subcategory
- Key points
- Steps
- Products or items
- Tags
- Useful-for context

AI providers must not return:

- Keep/remove recommendations
- Evergreen recommendations
- Batch action lists
- Unfavorite instructions

## Unfavorite Rules

Future batch unfavorite can only run after:

1. The user manually marks posts as `remove_from_xhs`.
2. The app shows the exact list.
3. The user confirms the exact list.
4. The app creates a local backup for each post.

If backup fails for a post, that post must be skipped.

## Obsidian Export Rules

Allowed exports:

- Daily review summaries, only when enabled.
- Manually selected evergreen notes.

Forbidden exports:

- Removed posts.
- Raw backups.
- Screenshots.
- Operation logs.
- Failed records.
- Full database dumps.
