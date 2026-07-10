import { Archive, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import {
  listPosts,
  updatePostCategory,
  updatePostNotes,
  updatePostStatus,
} from "../api.js";
import FilterBar from "../components/FilterBar.jsx";
import PostCard from "../components/PostCard.jsx";
import { useI18n } from "../i18n.jsx";

function Archived() {
  const { t } = useI18n();
  const [posts, setPosts] = useState([]);
  const [category, setCategory] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const filteredPosts = category ? posts.filter((post) => post.category === category) : posts;

  useEffect(() => {
    loadArchived();
  }, []);

  async function loadArchived() {
    setLoading(true);
    setMessage("");
    try {
      const data = await listPosts({ status: "archived" });
      setPosts(data.posts.filter((post) => post.xhs_favorite_status !== "unfavorited"));
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function restorePost(id) {
    const updated = await updatePostStatus(id, "keep");
    setPosts((current) => current.filter((post) => post.id !== updated.id));
    setMessage(t("archived.restored"));
  }

  async function handleStatusChange(id, reviewStatus) {
    const updated = await updatePostStatus(id, reviewStatus);
    if (updated.review_status === "archived") {
      setPosts((current) => current.map((post) => (post.id === id ? updated : post)));
    } else {
      setPosts((current) => current.filter((post) => post.id !== id));
      setMessage(t("archived.movedToRemove"));
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
          <h1>{t("archived.title")}</h1>
          <p>{t("archived.subtitle", { count: filteredPosts.length })}</p>
        </div>
        <button className="secondary-button" type="button" onClick={loadArchived} disabled={loading}>
          <RefreshCw size={18} aria-hidden="true" />
          <span>{t("daily.refresh")}</span>
        </button>
      </header>

      {message ? <div className="notice">{message}</div> : null}

      <FilterBar category={category} onCategoryChange={setCategory} onReset={() => setCategory("")} />

      <div className="post-grid">
        {filteredPosts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            mode="archived"
            onRestore={restorePost}
            onStatusChange={handleStatusChange}
            onNotesSave={handleNotesSave}
            onCategoryChange={handleCategoryChange}
          />
        ))}
      </div>

      {!loading && filteredPosts.length === 0 ? (
        <div className="empty-state">
          <Archive size={22} aria-hidden="true" />
          <span>{t("archived.empty")}</span>
        </div>
      ) : null}
    </section>
  );
}

export default Archived;
