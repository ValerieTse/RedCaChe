// RedCache background service worker (MV3, module).
// Orchestrates capture/unfavorite by driving a tab + the content script, and
// owns the extension-origin IndexedDB via the shared lib modules.
import { ingestFavorites, backfillTitle } from "./src/lib/ingest.js";
import * as db from "./src/lib/db.js";
import { SITE_MODES } from "./src/lib/selectors.js";

function waitForComplete(tabId, timeoutMs = 20000) {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    }, timeoutMs);
    function listener(id, info) {
      if (id === tabId && info.status === "complete") {
        clearTimeout(timer);
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    }
    chrome.tabs.onUpdated.addListener(listener);
  });
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function sendToTab(tabId, message, retries = 8) {
  for (let i = 0; i < retries; i += 1) {
    try {
      return await chrome.tabs.sendMessage(tabId, message);
    } catch {
      await sleep(500);
    }
  }
  throw new Error("content_script_unreachable");
}

// Open a tab, run fn(tabId), always close it afterward.
async function withTab(url, fn, { active = false } = {}) {
  const tab = await chrome.tabs.create({ url, active });
  try {
    await waitForComplete(tab.id);
    await sleep(1500);
    return await fn(tab.id);
  } finally {
    try {
      await chrome.tabs.remove(tab.id);
    } catch {
      /* tab already gone */
    }
  }
}

// Navigate an existing tab and wait for it to settle + content script ready.
async function navigateTab(tabId, url) {
  await chrome.tabs.update(tabId, { url });
  await waitForComplete(tabId);
  await sleep(1200);
}

async function doImport({ initialReviewStatus = "unreviewed" } = {}) {
  const config = await db.getConfig();
  if (!config.favorites_url) return { error: "no_favorites_url" };
  return withTab(
    config.favorites_url,
    async (tabId) => {
      const res = await sendToTab(tabId, { type: "scrapeFavorites", maxScrolls: 100 });
      if (!res?.ok) return { error: res?.error || "scrape_failed" };
      return ingestFavorites(res.payloads, {
        siteMode: config.site_mode,
        baseUrl: res.base_url,
        initialReviewStatus,
      });
    },
    { active: true },
  );
}

async function doDetectLogin() {
  const config = await db.getConfig();
  const site = SITE_MODES[config.site_mode] || SITE_MODES.rednote;
  return withTab(site.explore_url, async (tabId) => {
    const res = await sendToTab(tabId, { type: "detectLogin" });
    return { detected_state: res?.state || "unknown" };
  });
}

async function doDetectFavoritesUrl() {
  const config = await db.getConfig();
  const site = SITE_MODES[config.site_mode] || SITE_MODES.rednote;
  return withTab(site.explore_url, async (tabId) => {
    const res = await sendToTab(tabId, { type: "detectFavoritesUrl" });
    return { favorites_url: res?.url || "", status: res?.url ? "detected" : "not_found" };
  });
}

async function doBackfillTitles({ limit = 500 } = {}) {
  const posts = (await db.allPosts())
    .filter((p) => !p.title || p.title === "Untitled saved post")
    .slice(0, limit);
  if (posts.length === 0) return { scanned_count: 0, updated_count: 0, failed_count: 0 };
  const config = await db.getConfig();
  const site = SITE_MODES[config.site_mode] || SITE_MODES.rednote;
  let updated = 0;
  let failed = 0;
  const tab = await chrome.tabs.create({ url: site.explore_url, active: false });
  try {
    await waitForComplete(tab.id);
    for (const post of posts) {
      try {
        await navigateTab(tab.id, post.open_url || post.source_url);
        const res = await sendToTab(tab.id, { type: "extractTitle" });
        if (res?.ok && res.title && (await backfillTitle(post, res.title))) updated += 1;
        else failed += 1;
      } catch {
        failed += 1;
      }
    }
  } finally {
    try {
      await chrome.tabs.remove(tab.id);
    } catch {
      /* ignore */
    }
  }
  return { scanned_count: posts.length, updated_count: updated, failed_count: failed };
}

async function doUnfavorite({ postIds = [] } = {}) {
  const all = await db.allPosts();
  const targets = all.filter(
    (p) => p.review_status === "remove_from_xhs" && (postIds.length === 0 || postIds.includes(p.id)),
  );
  if (targets.length === 0) return { requested_count: 0, unfavorited_count: 0, failed_count: 0 };
  const config = await db.getConfig();
  const site = SITE_MODES[config.site_mode] || SITE_MODES.rednote;
  let unfavorited = 0;
  let failed = 0;
  const tab = await chrome.tabs.create({ url: site.explore_url, active: false });
  try {
    await waitForComplete(tab.id);
    for (const post of targets) {
      try {
        await navigateTab(tab.id, post.open_url || post.source_url);
        const res = await sendToTab(tab.id, { type: "toggleCollect" });
        if (res?.ok && res.result?.status === "unfavorited") {
          await db.updatePost(post.id, {
            review_status: "archived",
            xhs_favorite_status: "unfavorited",
            unfavorite_status: "unfavorited",
            restore_status: "restorable",
          });
          unfavorited += 1;
        } else {
          failed += 1;
        }
      } catch {
        failed += 1;
      }
    }
  } finally {
    try {
      await chrome.tabs.remove(tab.id);
    } catch {
      /* ignore */
    }
  }
  return { requested_count: targets.length, unfavorited_count: unfavorited, failed_count: failed };
}

const HANDLERS = {
  import: doImport,
  detectLogin: doDetectLogin,
  detectFavoritesUrl: doDetectFavoritesUrl,
  backfillTitles: doBackfillTitles,
  unfavorite: doUnfavorite,
};

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  const handler = HANDLERS[msg?.type];
  if (!handler) return false;
  handler(msg)
    .then((result) => sendResponse({ ok: true, result }))
    .catch((error) => sendResponse({ ok: false, error: String(error) }));
  return true; // async response
});
