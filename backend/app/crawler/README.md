# Crawler Placeholder

This directory contains the visible Playwright browser importer for RedCache.

The crawler must:

- Use a local visible Playwright browser session.
- Use a persistent local profile so the user can log in manually.
- Never ask for, collect, or store a Xiaohongshu password.
- Avoid CAPTCHA bypass, anti-bot bypass, private API signatures, or reverse-engineered private APIs.
- Import only content the user can already access in their own browser session.

The selector hints live in `selectors.py`. They are expected to need occasional
manual adjustment when Xiaohongshu changes page markup.
