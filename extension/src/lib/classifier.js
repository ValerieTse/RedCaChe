// Deterministic keyword classifier. Ported from backend/app/services/classifier.py.
import { CATEGORY_PRESETS, UNCATEGORIZED_SLUG } from "./categories.js";

// [{ name, keywords }] covering every built-in preset.
export const DEFAULT_CATEGORY_DEFS = CATEGORY_PRESETS.map((p) => ({
  name: p.slug,
  keywords: p.keywords,
}));

// Classify from the title only. Ties are broken by categoryDefs order.
export function classifyTitle(title, categoryDefs) {
  const defs = categoryDefs || DEFAULT_CATEGORY_DEFS;
  const haystack = String(title || "").trim().toLowerCase();
  let best = UNCATEGORIZED_SLUG;
  let bestScore = 0;
  for (const def of defs) {
    const keywords = def.keywords || [];
    let score = 0;
    for (const kw of keywords) {
      if (kw && haystack.includes(String(kw).toLowerCase())) score += 1;
    }
    if (score > bestScore) {
      bestScore = score;
      best = def.name;
    }
  }
  return best;
}

// Build classification defs from a config object { selected_category_slugs, custom_categories }.
export function classificationDefs(config) {
  const selected = new Set(config?.selected_category_slugs || []);
  const defs = [];
  for (const preset of CATEGORY_PRESETS) {
    if (selected.has(preset.slug)) defs.push({ name: preset.slug, keywords: preset.keywords });
  }
  for (const entry of config?.custom_categories || []) {
    const name = String(entry.name || entry.slug || "").trim();
    const keywords = (entry.keywords || []).map((k) => String(k).trim()).filter(Boolean);
    if (name && keywords.length) defs.push({ name, keywords });
  }
  return defs;
}

// Active categories (enabled presets + custom + Uncategorized) for dropdowns/filters.
export function activeCategories(config) {
  const selected = new Set(config?.selected_category_slugs || []);
  const out = [];
  for (const preset of CATEGORY_PRESETS) {
    if (selected.has(preset.slug)) out.push({ ...preset, is_custom: false });
  }
  const presetSlugs = new Set(CATEGORY_PRESETS.map((p) => p.slug));
  for (const entry of config?.custom_categories || []) {
    const name = String(entry.name || entry.slug || "").trim();
    if (name && !presetSlugs.has(name)) {
      out.push({
        slug: name,
        label_zh: name,
        label_en: name,
        keywords: (entry.keywords || []).map((k) => String(k).trim()).filter(Boolean),
        is_custom: true,
      });
    }
  }
  out.push({ slug: "Uncategorized", label_zh: "未分类", label_en: "Uncategorized", keywords: [], is_custom: false });
  return out;
}
