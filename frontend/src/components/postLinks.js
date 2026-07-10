export function resolvePostOpenUrl(post) {
  const payload = post?.raw_payload_json || {};
  const candidates = [
    post?.open_url,
    payload.open_url,
    ...(payload.observed_url_variants || []),
    post?.source_url,
  ].filter(Boolean);

  if (post?.import_source === "rednote") {
    const tokenizedUrl = candidates.find((url) => /[?&]xsec_token=/.test(url));
    if (tokenizedUrl) return tokenizedUrl;
    const detailUrl = candidates.find((url) => isRedNoteDetailUrl(url));
    if (detailUrl) return detailUrl;
    if (post?.note_id) return `https://www.rednote.com/explore/${post.note_id}`;
    return "";
  }

  return candidates[0] || "";
}

function isRedNoteDetailUrl(url) {
  try {
    const parsed = new URL(url);
    const host = parsed.hostname.replace(/^www\./, "");
    return host === "rednote.com" && /\/(user\/profile|explore)\//.test(parsed.pathname);
  } catch {
    return false;
  }
}
