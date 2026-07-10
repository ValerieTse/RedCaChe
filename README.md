# RedCache

Local-first app for managing saved Xiaohongshu / RedNote posts.

RedCache imports saved-post records, classifies them from their titles, lets you manually review each post, and can export selected records to an Obsidian vault path.

## What It Does

- Stores saved posts in local SQLite.
- Can open a visible Playwright Chromium browser with a persistent local profile for manual RedNote/Xiaohongshu login.
- Can best-effort import visible saved/favorites cards from the configured page.
- Uses fast deterministic title keywords for category assignment; video body text is not required.
- Lets you manually correct a category on any card; manual choices are preserved on later imports.
- Keeps review decisions manual: `unreviewed`, `keep`, `remove_from_xhs`, `evergreen`, or `archived`.
- Exports daily review summaries and manually selected evergreen notes to Markdown.
- Provides a React dashboard for filtering and reviewing imported posts.

## What It Does Not Do

- Does not ask for or store a Xiaohongshu password.
- Does not bypass CAPTCHA, anti-bot checks, private APIs, signatures, or platform restrictions.
- Does not let AI decide what to keep, remove, or evergreen.
- Does not unfavorite anything.
- Does not click unfavorite buttons.
- Does not export raw backups, removed archives, screenshots, operation logs, failed records, or database dumps to Obsidian.

## Install Backend

```bash
cd xhs-curator/backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m playwright install chromium
```

## Run Backend

```bash
cd xhs-curator/backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Run Mock Import

With the backend running:

```bash
curl -X POST http://127.0.0.1:8000/import/mock
```

Then list posts:

```bash
curl http://127.0.0.1:8000/posts
```

## Open Login Browser

RedCache has two site modes:

- Overseas / Global: `XHS_SITE_MODE=rednote`, opens `https://www.rednote.com/explore`
- Mainland China: `XHS_SITE_MODE=xiaohongshu`, opens `https://www.xiaohongshu.com/explore`

RedNote mode is the default. Set the mode in `.env` or your shell, restart the backend, then open a visible persistent browser:

```bash
curl -X POST http://127.0.0.1:8000/crawler/open-login
```

Log in manually inside the browser window. RedCache does not receive or store your password. Each mode gets a separate profile under `data/playwright-profile/`: `rednote` and `xiaohongshu`.

## Check Login Status

After logging in manually, go to the active explore URL in the visible browser, then run:

```bash
curl -X POST http://127.0.0.1:8000/crawler/check-login \
  -H "Content-Type: application/json" \
  -d '{}'
```

Only run visible import after `detected_state` is `logged_in`.

Profile diagnostics:

```bash
curl -X POST http://127.0.0.1:8000/crawler/debug-profile
```

## Run Visible Favorites Import

After manual login and a `logged_in` check, copy the actual saved/favorites URL from the logged-in browser and run:

```bash
curl -X POST http://127.0.0.1:8000/crawler/import-visible-favorites \
  -H "Content-Type: application/json" \
  -d '{"favorites_url":"https://www.rednote.com/YOUR_ACTUAL_SAVED_URL","max_scrolls":8}'
```

The import endpoint validates that the pasted URL matches the active domain. It stops with `domain_mismatch` if RedNote mode receives a Xiaohongshu URL or Xiaohongshu mode receives a RedNote URL.

The Settings page also has buttons for opening the login browser, checking login, debugging the profile, inspecting the saved/favorites page, and importing visible saved posts.

If a login page, CAPTCHA, security challenge, or unexpected page state appears, RedCache stops and returns a `stopped_reason`. Complete the challenge manually in the visible browser, then run import again.

## Source Links And Classification

Visible favorites import reads card-level information from the RedNote saved/favorites grid: title, author hints, thumbnail, and note URL. The dashboard displays covers in a consistent cropped `3:4` frame so cards stay the same size.

RedCache does not generate or display summaries. Categories are assigned from the post title only, so video posts can be organized without reading their body content. The supported categories are Beauty, Fashion, Fitness, Work, Study, Food, Travel, and Life. Titles with no matching signal use `Uncategorized` (shown as `未分类` in Chinese).

RedNote often exposes two URL variants for the same saved note:

- `source_url`: canonical URL with volatile query parameters removed. RedCache uses this for deduplication.
- `open_url`: original URL with query parameters such as `xsec_token` and `xsec_source=pc_collect`. RedCache prefers this when opening RedNote from the UI so the note can be resolved correctly.

If an older imported record has no `open_url`, run the visible favorites import again. Duplicate detection keeps the existing post and refreshes its openable RedNote URL.

## Daily Review Time Windows

RedNote does not reliably expose the time when a post was saved. RedCache therefore uses the time when a post was first fetched into the local SQLite database.

- Local baseline: `2026-07-09 22:30` in `America/Los_Angeles`.
- Posts fetched before the baseline are treated as previous/history and do not enter Daily Review.
- Without manual updates, Daily Review uses 24-hour windows measured from the baseline.
- Pressing **Update** closes a manual window from the previous Update time (or the baseline for the first Update) through the current time.
- Updating a duplicate only changes `last_seen_at`; it does not make an old post new again.

These defaults can be changed with `REVIEW_TIMEZONE` and `REVIEW_BASELINE_LOCAL`.

## Debugging RedNote Import

If RedNote login is verified but import returns `no_candidates_found`, inspect the saved/favorites page before changing selectors:

```bash
curl -X POST http://127.0.0.1:8000/crawler/inspect-page \
  -H "Content-Type: application/json" \
  -d '{
    "url":"https://www.rednote.com/user/profile/YOUR_PROFILE_ID?tab=fav&subTab=note",
    "max_scrolls":2,
    "save_debug_screenshot":true,
    "save_debug_html":true
  }'
```

Run `/crawler/check-login` first and confirm `detected_state` is `logged_in`. Use the actual saved/favorites URL copied from the logged-in visible browser.

Debug files are saved under `data/debug/rednote/`. Each inspection can include an initial screenshot, one screenshot after each scroll, a final HTML file, and a visible text dump.

Interpret the inspection counts this way:

- `total_links_count`: all links RedCache can see in the rendered page.
- `candidate_note_links_count`: links that match known RedNote note/detail URL patterns.
- `candidate_card_count`: note/card-like elements visible to selector or fallback diagnostics, including cards that may not expose normal links.

If `total_links_count > 0` but `candidate_note_links_count = 0`, adjust RedNote link patterns in `backend/app/crawler/selectors.py`. If `visible_text_sample` is login text, login did not persist for the active profile. If screenshots show cards but `candidate_card_count = 0`, adjust RedNote card selectors. If screenshots show blank or loading content, increase wait or scroll timing, then inspect again.

## Login Keeps Returning To Login Page

- Confirm `/crawler/settings` shows a stable absolute `profile_dir`.
- RedNote default profile path is `data/playwright-profile/rednote` under the project root.
- Xiaohongshu profile path is `data/playwright-profile/xiaohongshu` under the project root.
- Log in manually in the visible browser. RedCache does not handle your password.
- Overseas users should use RedNote mode and visit `https://www.rednote.com/explore`.
- Mainland users should use Xiaohongshu mode and visit `https://www.xiaohongshu.com/explore`.
- Run `/crawler/check-login` and wait for `detected_state: logged_in`.
- Try enabling system Chrome for normal browser compatibility:

```bash
export XHS_USE_SYSTEM_CHROME=true
```

Then restart the backend and open the login browser again.

- Use the actual favorites/saved URL copied from the logged-in browser, not a guessed URL.
- If CAPTCHA or a security challenge appears, handle it manually. RedCache will not bypass it.

## Adjust Selectors

RedNote/Xiaohongshu markup can change. Selector hints live in:

```text
backend/app/crawler/selectors.py
```

The importer also falls back to collecting links that look like note URLs, but title/author/thumbnail extraction may need manual selector adjustment over time.

## Install Frontend

```bash
cd xhs-curator/frontend
npm install
```

## Run Frontend

```bash
cd xhs-curator/frontend
npm run dev
```

Open the Vite URL, usually [http://localhost:5173](http://localhost:5173).

## Tests

```bash
cd xhs-curator/backend
pytest
```

## Still Mocked

- Category assignment uses deterministic title keywords rather than an LLM.
- Scheduled daily import is not implemented.
- Batch unfavorite is not implemented.
- Restore workflow is not implemented.
