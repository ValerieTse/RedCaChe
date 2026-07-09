import { Archive, Check, Circle, ExternalLink, Leaf, Save, Trash2 } from "lucide-react";
import { useState } from "react";
import StatusBadge from "./StatusBadge.jsx";

const statusActions = [
  { value: "unreviewed", label: "Unreviewed", icon: Circle },
  { value: "keep", label: "Keep", icon: Check },
  { value: "remove_from_xhs", label: "Remove", icon: Trash2 },
  { value: "evergreen", label: "Evergreen", icon: Leaf },
  { value: "archived", label: "Archive", icon: Archive },
];

function PostCard({ post, onStatusChange, onNotesSave }) {
  const [notes, setNotes] = useState(post.my_notes || "");
  const keyPoints = post.key_points_json || [];
  const tags = post.tags_json || [];
  const sourceLabel = post.import_source === "xiaohongshu" ? "Xiaohongshu" : "Mock";

  return (
    <article className="post-card">
      <header className="post-header">
        <div>
          <div className="post-meta">
            <span className={`source-pill source-${post.import_source || "mock"}`}>{sourceLabel}</span>
            <span>{post.category}</span>
            {post.sub_category ? <span>{post.sub_category}</span> : null}
          </div>
          <h2>{post.title}</h2>
        </div>
        <StatusBadge status={post.review_status} />
      </header>

      {post.thumbnail_url ? (
        <img className="post-thumbnail" src={post.thumbnail_url} alt="" loading="lazy" referrerPolicy="no-referrer" />
      ) : null}

      {post.ai_summary ? <p className="summary">{post.ai_summary}</p> : null}

      {keyPoints.length > 0 ? (
        <ul className="key-points">
          {keyPoints.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      ) : null}

      {tags.length > 0 ? (
        <div className="tag-row">
          {tags.map((tag) => (
            <span className="tag" key={tag}>
              {tag}
            </span>
          ))}
        </div>
      ) : null}

      <div className="post-link-row">
        <a href={post.source_url} target="_blank" rel="noreferrer">
          <ExternalLink size={16} aria-hidden="true" />
          Source
        </a>
      </div>

      <div className="status-actions" aria-label={`Manual status for ${post.title}`}>
        {statusActions.map((action) => {
          const Icon = action.icon;
          return (
            <button
              key={action.value}
              type="button"
              className={post.review_status === action.value ? "status-action selected" : "status-action"}
              onClick={() => onStatusChange(post.id, action.value)}
            >
              <Icon size={16} aria-hidden="true" />
              <span>{action.label}</span>
            </button>
          );
        })}
      </div>

      <div className="notes-row">
        <textarea
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="My notes"
          rows={3}
        />
        <button className="icon-button" type="button" onClick={() => onNotesSave(post.id, notes)} title="Save notes">
          <Save size={18} aria-hidden="true" />
        </button>
      </div>
    </article>
  );
}

export default PostCard;
