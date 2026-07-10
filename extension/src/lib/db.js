// IndexedDB-backed store for the pure extension. Mirrors the fields the React
// UI reads from the backend's Post/AppConfig, so the UI works unchanged.
import { ALL_PRESET_SLUGS } from "./categories.js";

const DB_NAME = "redcache";
const DB_VERSION = 1;

function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains("posts")) {
        const posts = db.createObjectStore("posts", { keyPath: "id", autoIncrement: true });
        posts.createIndex("note_id", "note_id", { unique: true });
        posts.createIndex("review_status", "review_status", { unique: false });
        posts.createIndex("category", "category", { unique: false });
      }
      if (!db.objectStoreNames.contains("config")) {
        db.createObjectStore("config", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("windows")) {
        db.createObjectStore("windows", { keyPath: "id", autoIncrement: true });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function tx(db, store, mode) {
  return db.transaction(store, mode).objectStore(store);
}

function reqToPromise(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

export async function allPosts() {
  const db = await openDb();
  return reqToPromise(tx(db, "posts", "readonly").getAll());
}

export async function getPost(id) {
  const db = await openDb();
  return reqToPromise(tx(db, "posts", "readonly").get(Number(id)));
}

export async function getPostByNoteId(noteId) {
  const db = await openDb();
  const idx = tx(db, "posts", "readonly").index("note_id");
  return reqToPromise(idx.get(noteId));
}

export async function putPost(post) {
  const db = await openDb();
  return reqToPromise(tx(db, "posts", "readwrite").put(post));
}

export async function putPosts(posts) {
  const db = await openDb();
  const store = tx(db, "posts", "readwrite");
  await Promise.all(posts.map((p) => reqToPromise(store.put(p))));
}

export async function updatePost(id, patch) {
  const post = await getPost(id);
  if (!post) return null;
  const updated = { ...post, ...patch, updated_at: new Date().toISOString() };
  await putPost(updated);
  return updated;
}

const DEFAULT_CONFIG = {
  id: 1,
  site_mode: "rednote",
  favorites_url: null,
  selected_category_slugs: ALL_PRESET_SLUGS,
  custom_categories: [],
  onboarding_completed: false,
  locale: "zh",
};

export async function getConfig() {
  const db = await openDb();
  const existing = await reqToPromise(tx(db, "config", "readonly").get(1));
  if (existing) return existing;
  await reqToPromise(tx(db, "config", "readwrite").put(DEFAULT_CONFIG));
  return { ...DEFAULT_CONFIG };
}

export async function patchConfig(patch) {
  const current = await getConfig();
  const next = { ...current, ...patch, id: 1 };
  const db = await openDb();
  await reqToPromise(tx(db, "config", "readwrite").put(next));
  return next;
}

export async function latestWindow() {
  const db = await openDb();
  const all = await reqToPromise(tx(db, "windows", "readonly").getAll());
  return all.sort((a, b) => new Date(b.ended_at) - new Date(a.ended_at))[0] || null;
}

export async function addWindow(win) {
  const db = await openDb();
  return reqToPromise(tx(db, "windows", "readwrite").add(win));
}
