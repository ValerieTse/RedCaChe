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

// Library shows kept posts plus the initial-import backlog awaiting review.
// Posts fetched later stay in Daily Review until the user picks a status.
function isLibraryPost(post) {
  if (post.review_status === "keep") return true;
  return post.review_status === "unreviewed" && post.from_initial_import;
}

function Dashboard() {
  const { t } = useI18n();
  const [posts, setPosts] = useState([]);
  const [total, setTotal] = useState(0);
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadPosts();
  }, [category]);

  async function loadPosts() {
    setLoading(true);
    setMessage("");
    try {
      const data = await listPosts({ category });
      const visiblePosts = data.posts.filter(isLibraryPost);
      setPosts(visiblePosts);
      setTotal(visiblePosts.length);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleStatusChange(id, reviewStatus) {
    const updated = await updatePostStatus(id, reviewStatus);
    if (!isLibraryPost(updated)) {
      setPosts((current) => current.filter((post) => post.id !== id));
      setTotal((current) => Math.max(0, current - 1));
    } else {
      setPosts((current) => current.map((post) => (post.id === id ? updated : post)));
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
          <h1>{t("dashboard.title")}</h1>
          <p>{t("dashboard.savedPosts", { count: total })}</p>
        </div>
      </header>

      <FilterBar
        category={category}
        onCategoryChange={setCategory}
        onReset={() => {
          setCategory("");
        }}
      />

      {message ? <div className="notice">{message}</div> : null}

      <div className="post-grid">
        {posts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            onStatusChange={handleStatusChange}
            onNotesSave={handleNotesSave}
            onCategoryChange={handleCategoryChange}
          />
        ))}
      </div>

      {!loading && posts.length === 0 ? <div className="empty-state">{t("dashboard.empty")}</div> : null}
    </section>
  );
}

export default Dashboard;
