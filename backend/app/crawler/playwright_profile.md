# Playwright Profile

RedCache launches Chromium with a persistent local profile directory:

```python
context = await chromium.launch_persistent_context(
    user_data_dir="data/playwright-profile",
    headless=False,
)
```

The user completes login and any CAPTCHA or platform challenge manually in the
visible browser. Automation stops when access is blocked, challenged, or
uncertain.
