import * as db from "./src/lib/db.js";
import { activeCategories } from "./src/lib/classifier.js";

const VIEWS = [
  { id: "daily", label: "每日整理", match: (p) => p.review_status === "unreviewed" && !p.from_initial_import },
  { id: "library", label: "资料库", match: (p) => p.review_status === "keep" || (p.review_status === "unreviewed" && p.from_initial_import) },
  { id: "evergreen", label: "长期保留", match: (p) => p.review_status === "evergreen" },
  { id: "remove", label: "移除复查", match: (p) => p.review_status === "remove_from_xhs" },
  { id: "archived", label: "归档", match: (p) => p.review_status === "archived" },
];
const STATUS_ACTIONS = [
  { value: "keep", label: "保留" },
  { value: "remove_from_xhs", label: "移除" },
  { value: "evergreen", label: "长期" },
  { value: "archived", label: "归档" },
];

let posts = [];
let config = { locale: "zh", selected_category_slugs: [], custom_categories: [] };
let currentView = "library";
let catFilter = "";

const $ = (id) => document.getElementById(id);
const catLabel = (slug) => {
  const c = activeCategories(config).find((x) => x.slug === slug);
  if (!c) return slug;
  return config.locale === "zh" ? c.label_zh : c.label_en;
};

function bestOpenUrl(p) {
  const payload = p.raw_payload_json || {};
  const cands = [p.open_url, payload.open_url, ...(payload.observed_url_variants || []), p.source_url].filter(Boolean);
  return cands.find((u) => /xsec_token=/.test(u)) || cands[0] || "";
}

async function refresh() {
  posts = await db.allPosts();
  config = await db.getConfig();
  renderNav();
  renderCatFilter();
  render();
}

function renderNav() {
  $("nav").innerHTML = "";
  for (const v of VIEWS) {
    const n = posts.filter(v.match).length;
    const b = document.createElement("button");
    b.className = "nav" + (v.id === currentView ? " on" : "");
    b.innerHTML = `${v.label}<span class="count">${n}</span>`;
    b.onclick = () => { currentView = v.id; render(); renderNav(); };
    $("nav").appendChild(b);
  }
}

function renderCatFilter() {
  const sel = $("catFilter");
  const cur = sel.value;
  sel.innerHTML = '<option value="">全部分类</option>';
  for (const c of activeCategories(config)) {
    const o = document.createElement("option");
    o.value = c.slug;
    o.textContent = catLabel(c.slug);
    sel.appendChild(o);
  }
  sel.value = cur;
}

function visiblePosts() {
  const view = VIEWS.find((v) => v.id === currentView);
  return posts
    .filter(view.match)
    .filter((p) => !catFilter || p.category === catFilter)
    .sort((a, b) => new Date(b.imported_at || 0) - new Date(a.imported_at || 0));
}

function render() {
  const view = VIEWS.find((v) => v.id === currentView);
  $("viewTitle").textContent = view.label;
  const list = visiblePosts();
  $("viewSub").textContent = `${list.length} 篇`;
  const grid = $("grid");
  grid.innerHTML = "";
  $("empty").hidden = list.length > 0;
  for (const p of list) grid.appendChild(renderCard(p));
}

function renderCard(p) {
  const el = document.createElement("article");
  el.className = "card";
  const openUrl = bestOpenUrl(p);
  const cats = activeCategories(config);
  const catOptions = cats.some((c) => c.slug === p.category) ? cats : [{ slug: p.category }, ...cats];
  const needsReview = p.review_status === "unreviewed";

  el.innerHTML = `
    <div class="thumb" style="${p.thumbnail_url ? `background-image:url('${p.thumbnail_url}')` : ""}"></div>
    <div class="body">
      <div class="meta">
        <select class="cat"></select>
        ${needsReview ? '<span class="badge">待判定</span>' : ""}
      </div>
      <div class="title">${escapeHtml(p.title || "Untitled saved post")}</div>
      ${p.author ? `<div class="author">${escapeHtml(p.author)}</div>` : ""}
      ${openUrl ? `<a class="link" href="${openUrl}" target="_blank" rel="noreferrer">打开原帖 ↗</a>` : ""}
      <div class="actions"></div>
    </div>`;

  const sel = el.querySelector(".cat");
  for (const c of catOptions) {
    const o = document.createElement("option");
    o.value = c.slug;
    o.textContent = catLabel(c.slug);
    sel.appendChild(o);
  }
  sel.value = p.category || "Uncategorized";
  sel.onchange = async () => {
    await db.updatePost(p.id, { category: sel.value, category_is_manual: true });
    await refresh();
  };

  const actions = el.querySelector(".actions");
  for (const a of STATUS_ACTIONS) {
    const b = document.createElement("button");
    b.textContent = a.label;
    if (p.review_status === a.value) b.className = "sel";
    b.onclick = async () => {
      await db.updatePost(p.id, { review_status: a.value });
      await refresh();
    };
    actions.appendChild(b);
  }
  return el;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

$("catFilter").addEventListener("change", (e) => { catFilter = e.target.value; render(); });
$("importBtn").addEventListener("click", async () => {
  const n = $("notice");
  n.hidden = false;
  n.textContent = "正在后台打开收藏页并导入…这可能要一两分钟。";
  $("importBtn").disabled = true;
  try {
    const res = await chrome.runtime.sendMessage({ type: "import" });
    if (!res?.ok) n.textContent = "出错:" + (res?.error || "failed");
    else if (res.result.error) n.textContent = "导入停止:" + res.result.error;
    else {
      n.textContent = `导入完成:新增 ${res.result.imported_count}、已存在 ${res.result.duplicate_count}。`;
      await refresh();
    }
  } catch (e) {
    n.textContent = "出错:" + e.message;
  } finally {
    $("importBtn").disabled = false;
  }
});

refresh();
