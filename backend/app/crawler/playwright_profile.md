# Playwright Profile

RedCache launches Chromium with a persistent local profile directory. The path
depends on `XHS_SITE_MODE` and is resolved relative to the project root:

- `XHS_SITE_MODE=rednote`: `data/playwright-profile/rednote`
- `XHS_SITE_MODE=xiaohongshu`: `data/playwright-profile/xiaohongshu`

```python
context = await chromium.launch_persistent_context(
    user_data_dir="data/playwright-profile/rednote",
    headless=False,
)
```

The user completes login and any CAPTCHA or platform challenge manually in the
visible browser. Automation stops when access is blocked, challenged, or
uncertain.

Overseas users should use RedNote mode and log in at
`https://www.rednote.com/explore`. Mainland users should use Xiaohongshu mode
and log in at `https://www.xiaohongshu.com/explore`.

Before import, run `/crawler/check-login` and confirm `detected_state` is
`logged_in`. Then paste the actual saved/favorites URL copied from the logged-in
browser; RedCache validates that the URL matches the active domain.

Set `XHS_USE_SYSTEM_CHROME=true` to prefer the installed Chrome channel. If it is
not available, RedCache falls back to bundled Chromium and reports that fallback
in `/crawler/debug-profile`.
