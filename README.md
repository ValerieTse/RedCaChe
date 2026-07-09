# RedCache

Local-first app for managing saved Xiaohongshu / RedNote posts.

RedCache imports saved-post records, runs mock AI summarization and classification, lets you manually review each post, and can export clean Markdown summaries to an Obsidian vault path.

## What It Does

- Stores saved posts in local SQLite.
- Can open a visible Playwright Chromium browser with a persistent local profile for manual Xiaohongshu login.
- Can best-effort import visible saved/favorites cards from the configured page.
- Runs a mock AI provider that returns summaries, categories, tags, key points, and useful context.
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

Start the backend, then open a visible persistent browser:

```bash
curl -X POST http://127.0.0.1:8000/crawler/open-login
```

Log in manually inside the browser window. RedCache does not receive or store your password. The profile is stored under `data/playwright-profile/` by default and is ignored by git.

## Run Visible Favorites Import

After manual login, run:

```bash
curl -X POST http://127.0.0.1:8000/crawler/import-visible-favorites \
  -H "Content-Type: application/json" \
  -d '{"favorites_url":"https://www.xiaohongshu.com/user/profile/me?tab=likes","max_scrolls":8}'
```

The Settings page also has buttons for opening the login browser and importing visible saved posts.

If a login page, CAPTCHA, security challenge, or unexpected page state appears, RedCache stops and returns a `stopped_reason`. Complete the challenge manually in the visible browser, then run import again.

## Adjust Selectors

Xiaohongshu markup can change. Selector hints live in:

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

- AI processing still uses the deterministic mock provider.
- Scheduled daily import is not implemented.
- Batch unfavorite is not implemented.
- Restore workflow is not implemented.
