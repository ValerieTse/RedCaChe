import * as db from "./src/lib/db.js";

const $ = (id) => document.getElementById(id);
const msgEl = $("msg");
function msg(text) {
  msgEl.hidden = !text;
  msgEl.textContent = text || "";
}
function setBusy(busy) {
  document.querySelectorAll("button").forEach((b) => (b.disabled = busy));
}
async function send(type, payload = {}) {
  const res = await chrome.runtime.sendMessage({ type, ...payload });
  if (!res?.ok) throw new Error(res?.error || "failed");
  return res.result;
}

async function load() {
  const config = await db.getConfig();
  $("siteMode").value = config.site_mode;
  $("favUrl").value = config.favorites_url || "";
}

$("siteMode").addEventListener("change", async (e) => {
  await db.patchConfig({ site_mode: e.target.value });
});
$("favUrl").addEventListener("change", async (e) => {
  await db.patchConfig({ favorites_url: e.target.value.trim() || null });
});

$("checkLogin").addEventListener("click", async () => {
  setBusy(true);
  msg("正在检查登录…");
  try {
    const r = await send("detectLogin");
    const ok = r.detected_state === "logged_in";
    $("loginStatus").innerHTML = ok
      ? '<span class="ok">✓ 已登录</span>'
      : `<span class="warn">未登录 (${r.detected_state})</span>`;
    msg(ok ? "已登录,可以导入了。" : "请先在浏览器里登录你的账号。");
  } catch (e) {
    msg("出错:" + e.message);
  } finally {
    setBusy(false);
  }
});

$("detectUrl").addEventListener("click", async () => {
  setBusy(true);
  msg("正在检测收藏夹地址…");
  try {
    const r = await send("detectFavoritesUrl");
    if (r.favorites_url) {
      $("favUrl").value = r.favorites_url;
      await db.patchConfig({ favorites_url: r.favorites_url });
      msg("已自动检测到收藏夹地址。");
    } else {
      msg("没检测到,请手动粘贴收藏夹地址。");
    }
  } catch (e) {
    msg("出错:" + e.message);
  } finally {
    setBusy(false);
  }
});

$("import").addEventListener("click", async () => {
  const favUrl = $("favUrl").value.trim();
  if (!favUrl) return msg("请先检测或填写收藏夹地址。");
  await db.patchConfig({ favorites_url: favUrl });
  setBusy(true);
  msg("正在后台打开收藏页并导入…这可能要一两分钟。");
  try {
    const r = await send("import");
    if (r.error) msg("导入停止:" + r.error);
    else {
      await db.patchConfig({ onboarding_completed: true });
      msg(`导入完成:新增 ${r.imported_count}、已存在 ${r.duplicate_count}、扫描 ${r.scanned_count}。\n点「打开资料库」查看。`);
    }
  } catch (e) {
    msg("出错:" + e.message);
  } finally {
    setBusy(false);
  }
});

$("backfill").addEventListener("click", async () => {
  setBusy(true);
  msg("正在补全缺失标题…逐篇打开原帖,较慢。");
  try {
    const r = await send("backfillTitles");
    msg(`标题补全:更新 ${r.updated_count}、失败 ${r.failed_count}(共 ${r.scanned_count})。`);
  } catch (e) {
    msg("出错:" + e.message);
  } finally {
    setBusy(false);
  }
});

$("openDash").addEventListener("click", () => {
  chrome.tabs.create({ url: chrome.runtime.getURL("dashboard.html") });
});

load();
