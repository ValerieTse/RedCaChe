"""Configurable selectors and page-state hints for visible RedNote/Xiaohongshu import.

Both sites can change markup often. Treat these selectors as editable hints,
not as a guarantee. The extractor also falls back to URL/text heuristics so
import does not depend on a single fragile selector.
"""

CARD_SELECTORS = [
    "section.note-item",
    "div.note-item",
    "div.feeds-page div.note-item",
    "a[href*='/explore/']",
    "a[href*='/discovery/item/']",
    "a[href*='/search_result/']",
]

XIAOHONGSHU_CARD_SELECTORS = CARD_SELECTORS

REDNOTE_CARD_SELECTORS = [
    "section.note-item",
    "div.note-item",
    "div[class*='note']",
    "section[class*='note']",
    "div[class*='card']",
    "a[href*='/explore/']",
    "a[href*='/discovery/item/']",
    "a[href*='/note/']",
    "a[href*='/item/']",
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

XIAOHONGSHU_LINK_PATH_HINTS = LINK_PATH_HINTS

REDNOTE_LINK_PATH_HINTS = [
    "/explore/",
    "/discovery/item/",
    "/search_result/",
    "/note/",
    "/notes/",
    "/item/",
    "/post/",
]

SITE_CARD_SELECTORS = {
    "rednote": REDNOTE_CARD_SELECTORS,
    "xiaohongshu": XIAOHONGSHU_CARD_SELECTORS,
}

SITE_LINK_PATH_HINTS = {
    "rednote": REDNOTE_LINK_PATH_HINTS,
    "xiaohongshu": XIAOHONGSHU_LINK_PATH_HINTS,
}

LOGIN_OR_CHALLENGE_URL_HINTS = [
    "login",
    "signin",
    "passport",
    "captcha",
    "verify",
    "security",
]

LOGIN_TEXT_HINTS = [
    "登录",
    "扫码登录",
    "手机号登录",
    "密码登录",
    "login",
    "sign in",
]

CHALLENGE_TEXT_HINTS = [
    "验证码",
    "安全验证",
    "滑动验证",
    "请完成验证",
    "captcha",
    "verify",
    "verification",
    "security check",
]

LOGIN_OR_CHALLENGE_TEXT_HINTS = [
    *LOGIN_TEXT_HINTS,
    *CHALLENGE_TEXT_HINTS,
]

AUTHENTICATED_TEXT_HINTS = [
    "消息",
    "通知",
    "发布",
    "创作中心",
    "我的",
    "退出登录",
    "个人主页",
]

AUTHENTICATED_SELECTOR_HINTS = [
    "a[href*='/user/profile/']",
    "[class*='avatar']",
    "[class*='user']",
    "[class*='profile']",
]
