// Selector / URL hints ported from backend/app/crawler/selectors.py.
export const REDNOTE_CARD_SELECTORS = [
  "section.note-item", "div.note-item", "div[class*='note']", "section[class*='note']",
  "div[class*='card']", "a[href*='/explore/']", "a[href*='/discovery/item/']",
  "a[href*='/note/']", "a[href*='/item/']",
];
export const XIAOHONGSHU_CARD_SELECTORS = [
  "section.note-item", "div.note-item", "div.feeds-page div.note-item",
  "a[href*='/explore/']", "a[href*='/discovery/item/']", "a[href*='/search_result/']",
];
export const SITE_CARD_SELECTORS = { rednote: REDNOTE_CARD_SELECTORS, xiaohongshu: XIAOHONGSHU_CARD_SELECTORS };

export const TITLE_SELECTORS = [".title", ".note-title", "[class*='title']"];
export const AUTHOR_SELECTORS = [".author", ".name", ".user-name", "[class*='author']", "[class*='name']"];

export const REDNOTE_LINK_PATH_HINTS = ["/explore/", "/discovery/item/", "/search_result/", "/note/", "/notes/", "/item/", "/post/"];
export const XIAOHONGSHU_LINK_PATH_HINTS = ["/explore/", "/discovery/item/", "/search_result/", "/item/"];
export const SITE_LINK_PATH_HINTS = { rednote: REDNOTE_LINK_PATH_HINTS, xiaohongshu: XIAOHONGSHU_LINK_PATH_HINTS };

export const LOGIN_TEXT_HINTS = ["登录", "扫码登录", "手机号登录", "密码登录", "login", "sign in"];
export const CHALLENGE_TEXT_HINTS = ["验证码", "安全验证", "滑动验证", "请完成验证", "captcha", "verify", "verification", "security check"];
export const AUTHENTICATED_TEXT_HINTS = ["消息", "通知", "发布", "创作中心", "我的", "退出登录", "个人主页"];

export const SITE_MODES = {
  rednote: { site_key: "rednote", display_name: "RedNote", base_url: "https://www.rednote.com", explore_url: "https://www.rednote.com/explore", domains: ["www.rednote.com", "rednote.com"] },
  xiaohongshu: { site_key: "xiaohongshu", display_name: "Xiaohongshu", base_url: "https://www.xiaohongshu.com", explore_url: "https://www.xiaohongshu.com/explore", domains: ["www.xiaohongshu.com", "xiaohongshu.com"] },
};
