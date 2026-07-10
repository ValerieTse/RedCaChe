import assert from "node:assert";
import { classifyTitle, classificationDefs, activeCategories } from "../src/lib/classifier.js";
import {
  canonicalizeSourceUrl,
  extractNoteIdFromUrl,
  looksLikeSiteNoteUrl,
  normalizeExtractedPost,
  dedupeExtractedPosts,
} from "../src/lib/extraction.js";

const RED = ["www.rednote.com", "rednote.com"];
const BARE = "https://www.rednote.com/user/profile/abc123/6964f682000000002103d9db";
const TOKEN = BARE + "?xsec_token=ABxx=&xsec_source=pc_collect";

// --- classifier ---
assert.equal(classifyTitle("夏季钩织背心"), "Handcraft", "knitting -> Handcraft");
assert.equal(classifyTitle("面试简历技巧"), "Work", "interview -> Work");
assert.equal(classifyTitle("贵阳美食探店"), "Food", "food");
assert.equal(classifyTitle("完全无关的东西"), "Uncategorized", "no signal -> Uncategorized");

// custom category classification
const cfg = { selected_category_slugs: ["Beauty"], custom_categories: [{ name: "航空", keywords: ["航空", "机场", "飞机"] }] };
assert.equal(classifyTitle("洛杉矶机场接送", classificationDefs(cfg)), "航空", "custom keyword -> custom category");
const active = activeCategories(cfg).map((c) => c.slug);
assert.ok(active.includes("Beauty") && active.includes("航空") && !active.includes("Fashion"), "active reflects selection");
assert.equal(active[active.length - 1], "Uncategorized", "Uncategorized last");

// --- extraction ---
assert.equal(extractNoteIdFromUrl(TOKEN), "6964f682000000002103d9db", "note id from profile url");
assert.equal(extractNoteIdFromUrl("https://www.rednote.com/explore/red123"), "red123", "note id from explore url");
assert.ok(looksLikeSiteNoteUrl(BARE, "rednote", RED), "rednote profile note is a note url");
assert.equal(canonicalizeSourceUrl(TOKEN), BARE, "source url strips query");

const n1 = normalizeExtractedPost({ source_url: BARE, title: "会呼吸的浪" }, { baseUrl: BARE, allowedDomains: RED, siteKey: "rednote" });
assert.equal(n1.note_id, "6964f682000000002103d9db");
assert.equal(n1.source_url, BARE);

// dedupe keeps the tokenized variant when the bare href is seen first
const bare = normalizeExtractedPost({ source_url: BARE }, { baseUrl: BARE, allowedDomains: RED, siteKey: "rednote" });
const tok = normalizeExtractedPost({ source_url: TOKEN }, { baseUrl: BARE, allowedDomains: RED, siteKey: "rednote" });
const { deduped, duplicateCount } = dedupeExtractedPosts([bare, tok]);
assert.equal(deduped.length, 1, "one unique post");
assert.equal(duplicateCount, 1, "one duplicate merged");
assert.ok(deduped[0].open_url.includes("xsec_token="), "tokenized variant kept after merge");

// non-note urls are dropped
assert.equal(
  normalizeExtractedPost({ source_url: "https://www.rednote.com/explore?channel=home" }, { baseUrl: BARE, allowedDomains: RED, siteKey: "rednote" }),
  null,
  "non-note url dropped",
);

console.log("extension lib tests passed");
