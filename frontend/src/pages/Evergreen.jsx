import { FileDown, Leaf } from "lucide-react";
import { useEffect, useState } from "react";
import { exportEvergreen, listPosts, updatePostNotes, updatePostStatus } from "../api.js";
import PostCard from "../components/PostCard.jsx";

function Evergreen() {
  const [posts, setPosts] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadEvergreen();
  }, []);

  async function loadEvergreen() {
    setLoading(true);
    try {
      const data = await listPosts({ status: "evergreen" });
      setPosts(data.posts);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleExport() {
    const result = await exportEvergreen(posts.map((post) => post.id));
    setMessage(`Exported ${result.exported_count} evergreen notes to ${result.output_path}`);
  }

  async function handleStatusChange(id, reviewStatus) {
    const updated = await updatePostStatus(id, reviewStatus);
    if (updated.review_status === "evergreen") {
      setPosts((current) => current.map((post) => (post.id === id ? updated : post)));
    } else {
      setPosts((current) => current.filter((post) => post.id !== id));
    }
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
          <h1>Evergreen</h1>
          <p>{posts.length} selected notes</p>
        </div>
        <button className="primary-button" type="button" onClick={handleExport} disabled={posts.length === 0}>
          <FileDown size={18} aria-hidden="true" />
          <span>Export</span>
        </button>
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
      {!loading && posts.length === 0 ? (
        <div className="empty-state">
          <Leaf size={22} aria-hidden="true" />
          <span>No evergreen notes yet.</span>
        </div>
      ) : null}
    </section>
  );
}

export default Evergreen;
