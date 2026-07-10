// URL canonicalization, note-id extraction, normalization and dedup.
// Ported from backend/app/crawler/extraction.py.
import { SITE_LINK_PATH_HINTS } from "./selectors.js";

const NOTE_ID_PATTERNS = [
  /\/user\/profile\/[A-Za-z0-9_-]+\/([A-Za-z0-9_-]+)/,
  /\/explore\/([A-Za-z0-9_-]+)/,
  /\/discovery\/item\/([A-Za-z0-9_-]+)/,
  /\/search_result\/([A-Za-z0-9_-]+)/,
  /\/notes?\/([A-Za-z0-9_-]+)/,
  /\/item\/([A-Za-z0-9_-]+)/,
  /\/post\/([A-Za-z0-9_-]+)/,
  /[?&](?:note_id|noteId|id)=([A-Za-z0-9_-]+)/,
];

export function canonicalizeUrl(url, baseUrl) {
  try {
    const u = new URL(url, baseUrl || "https://www.rednote.com/");
    u.hash = "";
    return u.href;
  } catch {
    return url || "";
  }
}

export function canonicalizeSourceUrl(url, baseUrl) {
  try {
    const u = new URL(canonicalizeUrl(url, baseUrl));
    u.search = "";
    u.hash = "";
    return u.href;
  } catch {
    return url || "";
  }
}

export function extractNoteIdFromUrl(url) {
  for (const pattern of NOTE_ID_PATTERNS) {
    const m = String(url || "").match(pattern);
    if (m) return m[1];
  }
  return null;
}

// Simple stable hash (FNV-1a) — the extension's own id space, need not match Python.
export function stableNoteIdFromUrl(url) {
  let h = 0x811c9dc5;
  const s = String(url || "");
  for (let i = 0; i < s.length; i += 1) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return "url_" + (h >>> 0).toString(16).padStart(8, "0");
}

function hostMatches(host, allowedDomains) {
  const h = String(host || "").toLowerCase().split(":")[0];
  return (allowedDomains || []).some((d) => h === d.toLowerCase() || h.endsWith("." + d.toLowerCase()));
}

function looksLikeRednoteProfileNotePath(pathname) {
  const segs = String(pathname || "").split("/").filter(Boolean);
  return segs.length >= 4 && segs[0] === "user" && segs[1] === "profile";
}

export function looksLikeSiteNoteUrl(url, siteKey, allowedDomains) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return false;
  }
  if (!hostMatches(parsed.hostname, allowedDomains)) return false;
  if (siteKey === "rednote" && looksLikeRednoteProfileNotePath(parsed.pathname)) return true;
  const hints = SITE_LINK_PATH_HINTS[siteKey] || SITE_LINK_PATH_HINTS.xiaohongshu;
  return hints.some((hint) => parsed.pathname.includes(hint));
}

function firstContentLine(text) {
  if (!text) return null;
  for (const raw of String(text).split(/[\n\r]+/)) {
    const line = raw.trim();
    if (line.length >= 2 && line.length <= 160) return line;
  }
  return null;
}

// payload: { source_url|href, open_url?, title?, author?, visible_text|text?, thumbnail_url?, note_id? }
export function normalizeExtractedPost(payload, { baseUrl, allowedDomains, siteKey } = {}) {
  const href = payload.source_url || payload.href;
  if (!href) return null;
  const openHref = payload.open_url || payload.original_url || href;
  const openUrl = canonicalizeUrl(String(openHref), baseUrl);
  const sourceUrl = canonicalizeSourceUrl(String(href), baseUrl);
  if (!looksLikeSiteNoteUrl(sourceUrl, siteKey, allowedDomains)) return null;

  const visibleText = String(payload.visible_text || payload.text || "").trim();
  const title = String(payload.title || firstContentLine(visibleText) || "").trim();
  let noteId = payload.note_id || extractNoteIdFromUrl(openUrl) || extractNoteIdFromUrl(sourceUrl);
  if (!noteId) noteId = stableNoteIdFromUrl(sourceUrl);

  const variants = [];
  for (const v of payload.observed_url_variants || []) {
    if (v) variants.push(canonicalizeUrl(String(v), baseUrl));
  }
  for (const v of [openUrl, sourceUrl]) {
    if (v && !variants.includes(v)) variants.push(v);
  }

  return {
    source_url: sourceUrl,
    open_url: openUrl,
    note_id: String(noteId),
    title: title || "Untitled saved post",
    author: payload.author || null,
    visible_text: visibleText || null,
    thumbnail_url: payload.thumbnail_url || payload.image_url || null,
    raw_payload: {
      ...payload,
      source_url: sourceUrl,
      open_url: openUrl,
      observed_url_variants: variants,
      note_id: String(noteId),
    },
  };
}

function openUrlHasQuery(url) {
  try {
    return Boolean(url && new URL(url).search);
  } catch {
    return false;
  }
}

export function mergeDuplicatePost(existing, duplicate) {
  if (openUrlHasQuery(duplicate.open_url) && !openUrlHasQuery(existing.open_url)) {
    existing.open_url = duplicate.open_url;
    existing.raw_payload.open_url = duplicate.open_url;
  }
  const variants = existing.raw_payload.observed_url_variants || [];
  for (const v of duplicate.raw_payload.observed_url_variants || []) {
    if (!variants.includes(v)) variants.push(v);
  }
  existing.raw_payload.observed_url_variants = variants;
}

export function dedupeExtractedPosts(posts) {
  const seenNoteIds = new Set();
  const seenUrls = new Set();
  const byNoteId = {};
  const byUrl = {};
  const deduped = [];
  let duplicateCount = 0;
  for (const post of posts) {
    if (seenNoteIds.has(post.note_id) || seenUrls.has(post.source_url)) {
      duplicateCount += 1;
      const existing = byNoteId[post.note_id] || byUrl[post.source_url];
      if (existing) mergeDuplicatePost(existing, post);
      continue;
    }
    seenNoteIds.add(post.note_id);
    seenUrls.add(post.source_url);
    byNoteId[post.note_id] = post;
    byUrl[post.source_url] = post;
    deduped.push(post);
  }
  return { deduped, duplicateCount };
}

export { openUrlHasQuery };
