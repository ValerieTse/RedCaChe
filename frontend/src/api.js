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

export function importMockPosts() {
  return request("/import/mock", { method: "POST" });
}

export function getDailyReview() {
  return request("/review/daily");
}

export function exportDailyReview() {
  return request("/export/obsidian/daily", { method: "POST" });
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

export function checkCrawlerLogin(url = null) {
  return request("/crawler/check-login", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function debugCrawlerProfile() {
  return request("/crawler/debug-profile", { method: "POST" });
}

export function importVisibleFavorites({ favoritesUrl, maxScrolls } = {}) {
  return request("/crawler/import-visible-favorites", {
    method: "POST",
    body: JSON.stringify({
      favorites_url: favoritesUrl || null,
      max_scrolls: maxScrolls || null,
    }),
  });
}

export { API_BASE };
