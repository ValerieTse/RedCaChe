// RedCache content script — runs inside logged-in xiaohongshu/rednote pages.
// It does the DOM work the Playwright layer used to do: scrape the favorites
// grid, read a note's title, and toggle the collect (favorite) button.
// It stores nothing; it hands raw payloads back to the extension via messaging.
(() => {
  const SITE = location.hostname.includes("xiaohongshu") ? "xiaohongshu" : "rednote";
  const ALLOWED = SITE === "rednote"
    ? ["www.rednote.com", "rednote.com"]
    : ["www.xiaohongshu.com", "xiaohongshu.com"];
  const LINK_HINTS = SITE === "rednote"
    ? ["/explore/", "/discovery/item/", "/search_result/", "/note/", "/notes/", "/item/", "/post/"]
    : ["/explore/", "/discovery/item/", "/search_result/", "/item/"];
  const CARD_SELECTORS = SITE === "rednote"
    ? ["section.note-item", "div.note-item", "div[class*='note']", "section[class*='note']", "div[class*='card']"]
    : ["section.note-item", "div.note-item", "div.feeds-page div.note-item"];
  const TITLE_SELECTORS = [".title", ".note-title", "[class*='title']"];
  const AUTHOR_SELECTORS = [".author", ".name", ".user-name", "[class*='author']", "[class*='name']"];
  const LOGIN_HINTS = ["登录", "扫码登录", "手机号登录", "密码登录", "sign in"];
  const AUTH_HINTS = ["消息", "通知", "发布", "创作中心", "我的", "退出登录", "个人主页"];

  const hostMatches = (host) => ALLOWED.some((d) => host === d || host.endsWith("." + d));
  const normalizeHref = (href) => {
    if (!href) return "";
    try { return new URL(href, location.href).href.split("#")[0]; } catch { return ""; }
  };
  const rednoteProfileNote = (url) => {
    const segs = url.pathname.split("/").filter(Boolean);
    return segs.length >= 4 && segs[0] === "user" && segs[1] === "profile";
  };
  const linkMatches = (href) => {
    const n = normalizeHref(href);
    if (!n) return false;
    let url; try { url = new URL(n); } catch { return false; }
    if (!hostMatches(url.hostname.toLowerCase())) return false;
    if (SITE === "rednote" && rednoteProfileNote(url)) return true;
    return LINK_HINTS.some((h) => url.pathname.includes(h));
  };
  const firstText = (root, selectors) => {
    for (const sel of selectors) {
      const t = root.querySelector(sel)?.innerText?.trim();
      if (t) return t;
    }
    return "";
  };
  const closestCard = (link) => {
    for (const sel of CARD_SELECTORS) {
      const node = link.closest(sel);
      if (node) return node;
    }
    let node = link;
    for (let i = 0; i < 4 && node?.parentElement; i += 1) node = node.parentElement;
    return node || link;
  };

  function collectCards() {
    const seen = new Set();
    const posts = [];
    for (const link of document.querySelectorAll("a[href]")) {
      const href = normalizeHref(link.getAttribute("href"));
      if (!linkMatches(href) || seen.has(href)) continue;
      seen.add(href);
      const card = closestCard(link);
      const image = card.querySelector("img");
      const text = card.innerText?.trim() || link.innerText?.trim() || "";
      const imageAlt = image ? (image.getAttribute("alt") || image.getAttribute("title") || "").trim() : "";
      const title =
        link.getAttribute("title")
        || link.getAttribute("aria-label")
        || firstText(card, TITLE_SELECTORS)
        || text.split(/\n+/).map((l) => l.trim()).find(Boolean)
        || imageAlt
        || "";
      posts.push({
        source_url: href,
        title,
        author: firstText(card, AUTHOR_SELECTORS),
        visible_text: text,
        thumbnail_url: image?.currentSrc || image?.src || image?.getAttribute("data-src") || "",
      });
    }
    return posts;
  }

  function scrollOnce() {
    const scrollables = Array.from(document.querySelectorAll("*")).filter((el) => {
      const s = getComputedStyle(el);
      return /(auto|scroll)/.test(s.overflowY + " " + s.overflow) && el.scrollHeight > el.clientHeight + 80;
    }).sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight));
    const doc = document.scrollingElement || document.documentElement;
    const docRange = Math.max(0, doc.scrollHeight - doc.clientHeight);
    const inner = scrollables[0] || null;
    const innerRange = inner ? Math.max(0, inner.scrollHeight - inner.clientHeight) : 0;
    const target = innerRange > docRange ? inner : doc;
    const delta = Math.max(window.innerHeight * 0.55, 360);
    if (target === document.body || target === document.documentElement || target === document.scrollingElement) {
      window.scrollBy(0, delta);
    } else {
      target.scrollTop += delta;
    }
    return Math.round(window.scrollY || doc.scrollTop || 0);
  }

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  async function scrapeFavorites(maxScrolls = 100) {
    const bySource = new Map();
    let idle = 0;
    let prev = null;
    for (let i = 0; i <= maxScrolls; i += 1) {
      for (const p of collectCards()) {
        if (!bySource.has(p.source_url)) bySource.set(p.source_url, p);
      }
      if (i >= maxScrolls) break;
      const pos = scrollOnce();
      if (pos === prev) idle += 1; else idle = 0;
      prev = pos;
      if (idle >= 6) break;
      await sleep(1000);
    }
    return { base_url: location.href, payloads: Array.from(bySource.values()) };
  }

  function extractTitle() {
    const clean = (v) => String(v || "").replace(/\s+/g, " ").replace(/\s*[-|·]\s*(rednote|小红书|xiaohongshu)\s*$/i, "").trim();
    const cands = [
      clean(document.querySelector("h1")?.innerText),
      clean(document.querySelector("meta[property='og:title']")?.getAttribute("content")),
      clean(document.title),
    ];
    for (const c of cands) {
      if (c && c.toLowerCase() !== "rednote" && c.length >= 2) return c;
    }
    return "";
  }

  function collectUseState() {
    const w = document.querySelector(".collect-wrapper");
    if (!w) return { found: false, href: "", visible: false };
    const u = w.querySelector("use");
    const href = (u && (u.getAttribute("xlink:href") || u.getAttribute("href"))) || "";
    const r = w.getBoundingClientRect();
    return { found: true, href, visible: r.width > 0 && r.height > 0 };
  }

  async function toggleCollect() {
    const state = collectUseState();
    if (!state.found) return { status: "failed", reason: "collect_button_not_found" };
    if (state.href === "#collect") return { status: "unfavorited", detail: "already_not_collected" };
    if (state.href !== "#collected") return { status: "failed", reason: "collect_state_unknown:" + (state.href || "empty") };
    if (!state.visible) return { status: "failed", reason: "collect_button_not_visible" };
    const wrapper = document.querySelector(".collect-wrapper");
    wrapper.scrollIntoView({ block: "center" });
    wrapper.click();
    for (let i = 0; i < 20; i += 1) {
      await sleep(150);
      if (collectUseState().href === "#collect") return { status: "unfavorited", detail: "toggled" };
    }
    return { status: "failed", reason: "collect_state_did_not_toggle" };
  }

  function detectLogin() {
    const body = (document.body?.innerText || "").toLowerCase();
    const url = location.href.toLowerCase();
    if (["captcha", "verify", "security"].some((h) => url.includes(h))) return "captcha_or_challenge";
    if (["login", "signin", "passport"].some((h) => url.includes(h))) return "login_required";
    if (LOGIN_HINTS.some((h) => body.includes(h.toLowerCase())) && !AUTH_HINTS.some((h) => body.includes(h))) return "login_required";
    if (AUTH_HINTS.some((h) => body.includes(h)) || document.querySelector("a[href*='/user/profile/']")) return "logged_in";
    return "unknown";
  }

  function detectFavoritesUrl() {
    const abs = (h) => { try { return new URL(h, location.href).href.split("?")[0]; } catch { return ""; } };
    for (const a of document.querySelectorAll("a[href]")) {
      const hasMe = Array.from(a.querySelectorAll("use")).some((u) => (u.getAttribute("xlink:href") || u.getAttribute("href")) === "#me");
      const href = a.getAttribute("href") || "";
      if (hasMe && /\/user\/profile\//.test(href)) {
        const base = abs(href).replace(/\/$/, "");
        return SITE === "rednote" ? base + "?tab=fav&subTab=note" : base + "?tab=fav";
      }
    }
    for (const a of document.querySelectorAll("a[href]")) {
      const href = a.getAttribute("href") || "";
      if (/\/user\/profile\/[0-9a-f]{20,}/i.test(href)) {
        const base = abs(href).replace(/\/$/, "");
        return SITE === "rednote" ? base + "?tab=fav&subTab=note" : base + "?tab=fav";
      }
    }
    return "";
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    (async () => {
      try {
        if (msg.type === "scrapeFavorites") sendResponse({ ok: true, ...(await scrapeFavorites(msg.maxScrolls)) });
        else if (msg.type === "extractTitle") sendResponse({ ok: true, title: extractTitle() });
        else if (msg.type === "toggleCollect") sendResponse({ ok: true, result: await toggleCollect() });
        else if (msg.type === "detectLogin") sendResponse({ ok: true, state: detectLogin(), site: SITE });
        else if (msg.type === "detectFavoritesUrl") sendResponse({ ok: true, url: detectFavoritesUrl(), site: SITE });
        else sendResponse({ ok: false, error: "unknown_message" });
      } catch (e) {
        sendResponse({ ok: false, error: String(e) });
      }
    })();
    return true; // keep the channel open for async response
  });
})();
