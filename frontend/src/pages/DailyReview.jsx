import { FileDown, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import {
  exportDailyReview,
  getDailyReview,
  updatePostNotes,
  updatePostStatus,
} from "../api.js";
import PostCard from "../components/PostCard.jsx";

function DailyReview() {
  const [posts, setPosts] = useState([]);
  const [reviewDate, setReviewDate] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadReview();
  }, []);

  async function loadReview() {
    setLoading(true);
    try {
      const data = await getDailyReview();
      setPosts(data.posts);
      setReviewDate(data.review_date);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleExport() {
    const result = await exportDailyReview();
    setMessage(`Exported ${result.exported_count} posts to ${result.output_path}`);
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
          <h1>Daily Review</h1>
          <p>{reviewDate || "Today"} · {posts.length} unreviewed</p>
        </div>
        <div className="button-row">
          <button className="secondary-button" type="button" onClick={loadReview} disabled={loading}>
            <RefreshCw size={18} aria-hidden="true" />
            <span>Refresh</span>
          </button>
          <button className="primary-button" type="button" onClick={handleExport}>
            <FileDown size={18} aria-hidden="true" />
            <span>Export</span>
          </button>
        </div>
      </header>

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
      {!loading && posts.length === 0 ? <div className="empty-state">Daily review is clear.</div> : null}
    </section>
  );
}

export default DailyReview;
