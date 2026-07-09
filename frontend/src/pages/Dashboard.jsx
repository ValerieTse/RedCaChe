import { DownloadCloud, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import {
  importMockPosts,
  listPosts,
  updatePostNotes,
  updatePostStatus,
} from "../api.js";
import FilterBar from "../components/FilterBar.jsx";
import PostCard from "../components/PostCard.jsx";

function Dashboard() {
  const [posts, setPosts] = useState([]);
  const [total, setTotal] = useState(0);
  const [category, setCategory] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadPosts();
  }, [category, status]);

  async function loadPosts() {
    setLoading(true);
    setMessage("");
    try {
      const data = await listPosts({ category, status });
      setPosts(data.posts);
      setTotal(data.total);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function runMockImport() {
    setLoading(true);
    try {
      const result = await importMockPosts();
      setMessage(`Imported ${result.imported_count}, updated ${result.updated_count}`);
      await loadPosts();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleStatusChange(id, reviewStatus) {
    const updated = await updatePostStatus(id, reviewStatus);
    setPosts((current) => current.map((post) => (post.id === id ? updated : post)));
  }

  async function handleNotesSave(id, notes) {
    const updated = await updatePostNotes(id, notes);
    setPosts((current) => current.map((post) => (post.id === id ? updated : post)));
    setMessage("Notes saved");
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p>{total} saved posts</p>
        </div>
        <button className="primary-button" type="button" onClick={runMockImport} disabled={loading}>
          {loading ? <RefreshCw className="spin" size={18} aria-hidden="true" /> : <DownloadCloud size={18} aria-hidden="true" />}
          <span>Import Mock</span>
        </button>
      </header>

      <FilterBar
        category={category}
        status={status}
        onCategoryChange={setCategory}
        onStatusChange={setStatus}
        onReset={() => {
          setCategory("");
          setStatus("");
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
          />
        ))}
      </div>

      {!loading && posts.length === 0 ? <div className="empty-state">No posts match the current filters.</div> : null}
    </section>
  );
}

export default Dashboard;
