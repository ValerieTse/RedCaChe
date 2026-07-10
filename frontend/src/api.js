const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

export function listPosts(filters = {}) {
  const params = new URLSearchParams();
  if (filters.category) params.set("category", filters.category);
  if (filters.status) params.set("status", filters.status);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request(`/posts${suffix}`);
}

export function searchBackupPosts(query = "") {
  const params = new URLSearchParams();
  if (query.trim()) params.set("q", query.trim());
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request(`/posts/backups/search${suffix}`);
}

export function updatePostStatus(id, reviewStatus) {
  return request(`/posts/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ review_status: reviewStatus }),
  });
}

export function updatePostNotes(id, myNotes) {
  return request(`/posts/${id}/notes`, {
    method: "PATCH",
    body: JSON.stringify({ my_notes: myNotes }),
  });
}

export function updatePostCategory(id, category) {
  return request(`/posts/${id}/category`, {
    method: "PATCH",
    body: JSON.stringify({ category }),
  });
}

export function importMockPosts() {
  return request("/import/mock", { method: "POST" });
}

export function getDailyReview() {
  return request("/review/daily");
}

export function updateDailyReview() {
  return request("/review/daily/update", { method: "POST" });
}

export function exportDailyReview(postIds = []) {
  return request("/export/obsidian/daily", {
    method: "POST",
    body: JSON.stringify({ post_ids: postIds }),
  });
}

export function listRemoveCheckPosts() {
  return request("/remove-check/posts");
}

export function restoreRemoveCheckPosts(postIds) {
  return request("/remove-check/restore", {
    method: "POST",
    body: JSON.stringify({ post_ids: postIds }),
  });
}

export function archiveRemoveCheckPosts(postIds) {
  return request("/remove-check/archive", {
    method: "POST",
    body: JSON.stringify({ post_ids: postIds }),
  });
}

export function confirmUnfavoritePosts(postIds) {
  return request("/remove-check/confirm-unfavorite", {
    method: "POST",
    body: JSON.stringify({ post_ids: postIds, confirm: true }),
  });
}

export function exportEvergreen(postIds = null) {
  return request("/export/obsidian/evergreen", {
    method: "POST",
    body: JSON.stringify({ post_ids: postIds }),
  });
}

export function getCrawlerSettings() {
  return request("/crawler/settings");
}

export function openCrawlerLogin(loginUrl = null) {
  return request("/crawler/open-login", {
    method: "POST",
    body: JSON.stringify({ login_url: loginUrl }),
  });
}

export function openPostSource(postId) {
  return request("/crawler/open-post", {
    method: "POST",
    body: JSON.stringify({ post_id: postId }),
  });
}

export function checkCrawlerLogin(url = null) {
  return request("/crawler/check-login", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function debugCrawlerProfile() {
  return request("/crawler/debug-profile", { method: "POST" });
}

export function inspectCrawlerPage({
  url,
  maxScrolls = 2,
  saveDebugScreenshot = true,
  saveDebugHtml = true,
} = {}) {
  return request("/crawler/inspect-page", {
    method: "POST",
    body: JSON.stringify({
      url,
      max_scrolls: maxScrolls,
      save_debug_screenshot: saveDebugScreenshot,
      save_debug_html: saveDebugHtml,
    }),
  });
}

export function importVisibleFavorites({ favoritesUrl, maxScrolls, initialReviewStatus, headless } = {}) {
  return request("/crawler/import-visible-favorites", {
    method: "POST",
    body: JSON.stringify({
      favorites_url: favoritesUrl || null,
      max_scrolls: maxScrolls || null,
      initial_review_status: initialReviewStatus || undefined,
      headless: headless || false,
    }),
  });
}

export function getConfig() {
  return request("/config");
}

export function patchConfig(patch) {
  return request("/config", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function getCategories() {
  return request("/categories");
}

export function getCategoryPresets() {
  return request("/categories/presets");
}

export function reclassifyPosts() {
  return request("/categories/reclassify", { method: "POST" });
}

export function detectFavoritesUrl() {
  return request("/crawler/detect-favorites-url", { method: "POST" });
}

export { API_BASE };
