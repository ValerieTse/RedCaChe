// Ingest pipeline: mirrors backend _save_posts + import dedup/token-refresh.
import {
  normalizeExtractedPost,
  dedupeExtractedPosts,
  openUrlHasQuery,
} from "./extraction.js";
import { classifyTitle, classificationDefs } from "./classifier.js";
import { SITE_MODES } from "./selectors.js";
import * as db from "./db.js";

export async function ingestFavorites(rawPayloads, { siteMode = "rednote", baseUrl, initialReviewStatus = "unreviewed" } = {}) {
  const site = SITE_MODES[siteMode] || SITE_MODES.rednote;
  const config = await db.getConfig();
  const defs = classificationDefs(config);

  const normalized = rawPayloads
    .map((p) => normalizeExtractedPost(p, { baseUrl: baseUrl || site.base_url, allowedDomains: site.domains, siteKey: site.site_key }))
    .filter(Boolean);
  const { deduped, duplicateCount } = dedupeExtractedPosts(normalized);

  const existingAll = await db.allPosts();
  const isInitial = existingAll.filter((p) => p.import_source !== "mock").length === 0;
  const byNoteId = new Map(existingAll.map((p) => [p.note_id, p]));
  const bySource = new Map(existingAll.map((p) => [p.source_url, p]));

  let imported = 0;
  let dbDup = 0;
  let failed = 0;
  const now = new Date().toISOString();

  for (const ex of deduped) {
    try {
      const existing = byNoteId.get(ex.note_id) || bySource.get(ex.source_url);
      if (existing) {
        dbDup += 1;
        if (ex.open_url && (!existing.open_url || existing.open_url === existing.source_url || openUrlHasQuery(ex.open_url))) {
          existing.open_url = ex.open_url; // refresh expiring xsec_token
        }
        existing.last_seen_at = now;
        existing.updated_at = now;
        if (initialReviewStatus === "keep" && existing.review_status === "unreviewed") existing.review_status = "keep";
        await db.putPost(existing);
        continue;
      }
      const post = {
        note_id: ex.note_id,
        source_url: ex.source_url,
        open_url: ex.open_url || ex.source_url,
        import_source: site.site_key,
        thumbnail_url: ex.thumbnail_url,
        raw_payload_json: ex.raw_payload,
        title: ex.title,
        author: ex.author,
        imported_at: now,
        last_seen_at: now,
        raw_text: ex.visible_text,
        ai_summary: null,
        category: classifyTitle(ex.title, defs),
        category_is_manual: false,
        sub_category: null,
        key_points_json: [],
        step_by_step_json: [],
        products_or_items_json: [],
        useful_for: null,
        tags_json: [],
        my_notes: null,
        review_status: initialReviewStatus,
        from_initial_import: isInitial,
        xhs_favorite_status: "favorited",
        backup_status: null,
        restore_status: "not_needed",
        unfavorite_status: "not_requested",
        screenshot_paths_json: [],
        operation_logs_json: [],
        enrichment_status: "not_enriched",
        enriched_at: null,
        created_at: now,
        updated_at: now,
      };
      await db.putPost(post);
      imported += 1;
    } catch {
      failed += 1;
    }
  }

  return {
    scanned_count: normalized.length,
    imported_count: imported,
    duplicate_count: duplicateCount + dbDup,
    failed_count: failed,
  };
}

// Fill titles for posts still on the fallback, re-classifying non-manual ones.
export async function backfillTitle(post, title) {
  if (!title) return false;
  const config = await db.getConfig();
  const defs = classificationDefs(config);
  const patch = { title: title.slice(0, 512) };
  if (!post.category_is_manual) patch.category = classifyTitle(title, defs);
  await db.updatePost(post.id, patch);
  return true;
}
