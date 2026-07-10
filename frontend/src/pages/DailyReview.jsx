import { FileDown, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import {
  exportDailyReview,
  getDailyReview,
  updateDailyReview,
  updatePostCategory,
  updatePostNotes,
  updatePostStatus,
} from "../api.js";
import FilterBar from "../components/FilterBar.jsx";
import PostCard from "../components/PostCard.jsx";
import { useI18n } from "../i18n.jsx";

const hiddenReviewStatuses = new Set(["keep", "remove_from_xhs", "archived", "evergreen"]);

function DailyReview() {
  const { language, t } = useI18n();
  const [posts, setPosts] = useState([]);
  const [reviewDate, setReviewDate] = useState("");
  const [reviewWindow, setReviewWindow] = useState(null);
  const [category, setCategory] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const filteredPosts = category ? posts.filter((post) => post.category === category) : posts;

  useEffect(() => {
    loadReview();
  }, []);

  async function loadReview() {
    setLoading(true);
    try {
      const data = await getDailyReview();
      setPosts(data.posts);
      setReviewDate(data.review_date);
      setReviewWindow(data);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleUpdate() {
    setLoading(true);
    setMessage("");
    try {
      const data = await updateDailyReview();
      setPosts(data.posts);
      setReviewDate(data.review_date);
      setReviewWindow(data);
      setMessage(t("daily.updated", { count: data.count }));
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleExport() {
    const result = await exportDailyReview(filteredPosts.map((post) => post.id));
    setMessage(t("daily.exported", { count: result.exported_count, path: result.output_path }));
  }

  async function handleStatusChange(id, reviewStatus) {
    const updated = await updatePostStatus(id, reviewStatus);
    if (hiddenReviewStatuses.has(updated.review_status)) {
      setPosts((current) => current.filter((post) => post.id !== id));
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
          <h1>{t("daily.title")}</h1>
          <p>{formatReviewWindow(reviewWindow, language, t, reviewDate)} · {t("daily.count", { count: posts.length })}</p>
        </div>
        <div className="button-row">
          <button className="secondary-button" type="button" onClick={handleUpdate} disabled={loading}>
            <RefreshCw size={18} aria-hidden="true" />
            <span>{t("daily.update")}</span>
          </button>
          <button className="primary-button" type="button" onClick={handleExport} disabled={filteredPosts.length === 0}>
            <FileDown size={18} aria-hidden="true" />
            <span>{t("daily.export")}</span>
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
            onStatusChange={handleStatusChange}
            onNotesSave={handleNotesSave}
            onCategoryChange={handleCategoryChange}
          />
        ))}
      </div>
      {!loading && filteredPosts.length === 0 ? <div className="empty-state">{t("daily.clear")}</div> : null}
    </section>
  );
}

function formatReviewWindow(reviewWindow, language, t, fallbackDate) {
  if (!reviewWindow?.window_start || !reviewWindow?.window_end) {
    return fallbackDate || t("daily.today");
  }
  const start = new Date(reviewWindow.window_start);
  const end = new Date(reviewWindow.window_end);
  const formatter = new Intl.DateTimeFormat(language === "zh" ? "zh-CN" : "en-US", {
    month: "numeric",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: reviewWindow.timezone,
  });
  if (start.getTime() === end.getTime()) {
    return t("daily.startsAt", { time: formatter.format(start) });
  }
  const mode = reviewWindow.window_mode === "manual_update" ? t("daily.manualWindow") : t("daily.automaticWindow");
  return t("daily.window", { start: formatter.format(start), end: formatter.format(end), mode });
}

export default DailyReview;
