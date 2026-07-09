# RedCache

Local-first app for managing saved Xiaohongshu / RedNote posts.

RedCache imports saved-post records, runs mock AI summarization and classification, lets you manually review each post, and can export clean Markdown summaries to an Obsidian vault path.

## What It Does

- Stores saved posts in local SQLite.
- Can open a visible Playwright Chromium browser with a persistent local profile for manual RedNote/Xiaohongshu login.
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

The Settings page also has buttons for opening the login browser, checking login, debugging the profile, and importing visible saved posts.

If a login page, CAPTCHA, security challenge, or unexpected page state appears, RedCache stops and returns a `stopped_reason`. Complete the challenge manually in the visible browser, then run import again.

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

- AI processing still uses the deterministic mock provider.
- Scheduled daily import is not implemented.
- Batch unfavorite is not implemented.
- Restore workflow is not implemented.
