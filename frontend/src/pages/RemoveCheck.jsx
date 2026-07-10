import { Archive, CheckSquare, RefreshCw, RotateCcw, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  archiveRemoveCheckPosts,
  confirmUnfavoritePosts,
  listRemoveCheckPosts,
  restoreRemoveCheckPosts,
  updatePostCategory,
  updatePostNotes,
} from "../api.js";
import FilterBar from "../components/FilterBar.jsx";
import PostCard from "../components/PostCard.jsx";
import { useI18n } from "../i18n.jsx";

function RemoveCheck() {
  const { t } = useI18n();
  const [posts, setPosts] = useState([]);
  const [category, setCategory] = useState("");
  const [selectedIds, setSelectedIds] = useState(() => new Set());
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const filteredPosts = useMemo(
    () => (category ? posts.filter((post) => post.category === category) : posts),
    [category, posts],
  );
  const selectedPostIds = useMemo(
    () => filteredPosts.filter((post) => selectedIds.has(post.id)).map((post) => post.id),
    [filteredPosts, selectedIds],
  );
  const selectedCount = selectedPostIds.length;
  const allSelected = filteredPosts.length > 0 && selectedCount === filteredPosts.length;

  useEffect(() => {
    loadPosts();
  }, []);

  async function loadPosts() {
    setLoading(true);
    setMessage("");
    try {
      const data = await listRemoveCheckPosts();
      setPosts(data.posts);
      setSelectedIds((current) => new Set(data.posts.filter((post) => current.has(post.id)).map((post) => post.id)));
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  function toggleSelected(id, checked) {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (checked) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  function toggleSelectAll() {
    const visibleIds = new Set(filteredPosts.map((post) => post.id));
    setSelectedIds((current) => {
      const next = new Set(current);
      if (allSelected) {
        for (const id of visibleIds) next.delete(id);
      } else {
        for (const id of visibleIds) next.add(id);
      }
      return next;
    });
  }

  async function archivePosts(ids) {
    if (ids.length === 0) return;
    setLoading(true);
    try {
      const result = await archiveRemoveCheckPosts(ids);
      setMessage(t("remove.archived", { count: result.archived_count }));
      await loadPosts();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function restorePosts(ids) {
    if (ids.length === 0) return;
    setLoading(true);
    try {
      const result = await restoreRemoveCheckPosts(ids);
      setMessage(t("remove.restored", { count: result.restored_count }));
      await loadPosts();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function confirmRemoval() {
    if (selectedPostIds.length === 0) return;
    const ok = window.confirm(t("remove.confirmPrompt", { count: selectedPostIds.length }));
    if (!ok) return;
    setLoading(true);
    try {
      const result = await confirmUnfavoritePosts(selectedPostIds);
      setMessage(
        result.stopped_reason
          ? t("remove.confirmStopped", { reason: result.stopped_reason })
          : t("remove.confirmed", {
              unfavorited: result.unfavorited_count,
              failed: result.failed_count,
              backedUp: result.backed_up_count,
            }),
      );
      await loadPosts();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleNotesSave(id, notes) {
    const updated = await updatePostNotes(id, notes);
    setPosts((current) => current.map((post) => (post.id === id ? updated : post)));
    setMessage(t("common.notesSaved"));
  }

  async function handleCategoryChange(id, nextCategory) {
    const updated = await updatePostCategory(id, nextCategory);
    setPosts((current) => current.map((post) => (post.id === id ? updated : post)));
    setMessage(t("post.categorySaved"));
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>{t("remove.title")}</h1>
          <p>{t("remove.subtitle", { count: filteredPosts.length })}</p>
        </div>
        <div className="button-row">
          <button className="secondary-button" type="button" onClick={loadPosts} disabled={loading}>
            <RefreshCw size={18} aria-hidden="true" />
            <span>{t("daily.refresh")}</span>
          </button>
          <button className="secondary-button" type="button" onClick={toggleSelectAll} disabled={filteredPosts.length === 0}>
            <CheckSquare size={18} aria-hidden="true" />
            <span>{allSelected ? t("remove.clearSelection") : t("remove.selectAll")}</span>
          </button>
          <button className="secondary-button" type="button" onClick={() => restorePosts(selectedPostIds)} disabled={selectedCount === 0 || loading}>
            <RotateCcw size={18} aria-hidden="true" />
            <span>{t("remove.restore")}</span>
          </button>
          <button className="secondary-button" type="button" onClick={() => archivePosts(selectedPostIds)} disabled={selectedCount === 0 || loading}>
            <Archive size={18} aria-hidden="true" />
            <span>{t("status.archived")}</span>
          </button>
          <button className="danger-button" type="button" onClick={confirmRemoval} disabled={selectedCount === 0 || loading}>
            <Trash2 size={18} aria-hidden="true" />
            <span>{t("remove.confirm")}</span>
          </button>
        </div>
      </header>

      {message ? <div className="notice">{message}</div> : null}

      <FilterBar category={category} onCategoryChange={setCategory} onReset={() => setCategory("")} />

      <div className="post-grid">
        {filteredPosts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            mode="remove-check"
            selected={selectedIds.has(post.id)}
            onSelectChange={toggleSelected}
            onArchive={(id) => archivePosts([id])}
            onRestore={(id) => restorePosts([id])}
            onNotesSave={handleNotesSave}
            onCategoryChange={handleCategoryChange}
          />
        ))}
      </div>

      {!loading && filteredPosts.length === 0 ? (
        <div className="empty-state">
          <Trash2 size={22} aria-hidden="true" />
          <span>{t("remove.empty")}</span>
        </div>
      ) : null}
    </section>
  );
}

export default RemoveCheck;
