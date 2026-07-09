"""Configurable selectors and page-state hints for visible Xiaohongshu import.

Xiaohongshu changes markup often. Treat these selectors as editable hints, not
as a guarantee. The extractor also falls back to URL/text heuristics so import
does not depend on a single fragile selector.
"""

CARD_SELECTORS = [
    "section.note-item",
    "div.note-item",
    "div.feeds-page div.note-item",
    "a[href*='/explore/']",
    "a[href*='/discovery/item/']",
    "a[href*='/search_result/']",
]

AUTHOR_SELECTORS = [
    ".author",
    ".name",
    ".user-name",
    "[class*='author']",
    "[class*='name']",
]

TITLE_SELECTORS = [
    ".title",
    ".note-title",
    "[class*='title']",
]

LINK_PATH_HINTS = [
    "/explore/",
    "/discovery/item/",
    "/search_result/",
    "/item/",
]

LOGIN_OR_CHALLENGE_URL_HINTS = [
    "login",
    "signin",
    "passport",
    "captcha",
    "verify",
    "security",
]

LOGIN_OR_CHALLENGE_TEXT_HINTS = [
    "登录",
    "扫码登录",
    "验证码",
    "安全验证",
    "滑动验证",
    "请完成验证",
    "captcha",
    "verify",
    "verification",
    "security check",
]
