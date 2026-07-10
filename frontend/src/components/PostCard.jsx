import { Archive, Check, ExternalLink, Leaf, Pencil, RotateCcw, Save, Trash2 } from "lucide-react";
import { useState } from "react";
import { openPostSource } from "../api.js";
import { useCategories } from "../CategoriesContext.jsx";
import { useI18n } from "../i18n.jsx";
import { resolvePostOpenUrl } from "./postLinks.js";

const statusActions = [
  { value: "keep", icon: Check },
  { value: "remove_from_xhs", icon: Trash2 },
  { value: "evergreen", icon: Leaf },
  { value: "archived", icon: Archive },
];

const removeCheckActions = [
  { value: "restore", icon: RotateCcw, labelKey: "remove.restore" },
  { value: "archived", icon: Archive, labelKey: "status.archived" },
];

const archivedActions = [
  { value: "restore", icon: RotateCcw, labelKey: "remove.restore" },
  { value: "remove_from_xhs", icon: Trash2, labelKey: "status.remove_from_xhs" },
];

function PostCard({
  post,
  onStatusChange,
  onNotesSave,
  onCategoryChange,
  mode = "review",
  selected = false,
  onSelectChange,
  onArchive,
  onRestore,
}) {
  const { t } = useI18n();
  const { categories, labelFor } = useCategories();
  const [notes, setNotes] = useState(post.my_notes || "");
  const [openingSource, setOpeningSource] = useState(false);
  const openUrl = resolvePostOpenUrl(post);
  const category = post.category && post.category !== "Other" ? post.category : "Uncategorized";
  // Keep the post's current category selectable even if it was later disabled.
  const categoryOptions = categories.some((item) => item.slug === category)
    ? categories
    : [{ slug: category }, ...categories];
  const isRemoveCheck = mode === "remove-check";
  const isArchived = mode === "archived";
  const isQueuePage = isRemoveCheck || isArchived;

  const cardClassName = [
    "post-card",
    isQueuePage ? "queue-card" : "",
    isQueuePage && selected ? "selected-for-removal" : "",
  ].filter(Boolean).join(" ");

  async function handleOpenSource() {
    if (!openUrl || openingSource) return;
    setOpeningSource(true);
    try {
      await openPostSource(post.id);
    } catch {
      // Intentionally silent: the visible browser window is the only feedback.
    } finally {
      setOpeningSource(false);
    }
  }

  return (
    <article className={cardClassName}>
      {isRemoveCheck ? (
        <label className="card-select">
          <input
            type="checkbox"
            checked={selected}
            onChange={(event) => onSelectChange?.(post.id, event.target.checked)}
          />
          <span>{t("remove.selectPost")}</span>
        </label>
      ) : null}
      {post.thumbnail_url ? (
        <img
          className="post-thumbnail"
          src={post.thumbnail_url}
          alt={post.title}
          loading="lazy"
          referrerPolicy="no-referrer"
        />
      ) : null}

      <div className="post-card-body">
        <header className="post-header">
          <div>
            <div className="post-meta">
              <label className="category-control">
                <Pencil size={14} aria-hidden="true" />
                <span className="sr-only">{t("post.editCategory")}</span>
                <select
                  value={category}
                  onChange={(event) => onCategoryChange(post.id, event.target.value)}
                  aria-label={t("post.editCategoryFor", { title: post.title })}
                >
                  {categoryOptions.map((item) => (
                    <option value={item.slug} key={item.slug}>
                      {labelFor(item.slug)}
                    </option>
                  ))}
                </select>
              </label>
              {post.category_is_manual ? <span className="manual-category">{t("post.manualCategory")}</span> : null}
              {!isQueuePage && post.review_status === "unreviewed" ? (
                <span className="unreviewed-badge">{t("post.unreviewed")}</span>
              ) : null}
            </div>
            <h2>{post.title}</h2>
            {post.author ? <p className="post-author">{t("post.byAuthor", { author: post.author })}</p> : null}
          </div>
        </header>

        <div className="post-link-row">
          {openUrl ? (
            <button type="button" className="link-button" onClick={handleOpenSource} disabled={openingSource}>
              <ExternalLink size={16} aria-hidden="true" />
              {t("post.openSource")}
            </button>
          ) : (
            <span>{t("post.sourceUnavailable")}</span>
          )}
        </div>

        {isRemoveCheck ? (
          <div className="status-actions remove-actions" aria-label={t("remove.actionsFor", { title: post.title })}>
            {removeCheckActions.map((action) => {
              const Icon = action.icon;
              return (
                <button
                  key={action.value}
                  type="button"
                  className="status-action"
                  onClick={() => (action.value === "archived" ? onArchive?.(post.id) : onRestore?.(post.id))}
                  title={t(action.labelKey)}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span>{t(action.labelKey)}</span>
                </button>
              );
            })}
          </div>
        ) : isArchived ? (
          <div className="status-actions remove-actions" aria-label={t("archived.actionsFor", { title: post.title })}>
            {archivedActions.map((action) => {
              const Icon = action.icon;
              return (
                <button
                  key={action.value}
                  type="button"
                  className="status-action"
                  onClick={() => (action.value === "restore" ? onRestore?.(post.id) : onStatusChange?.(post.id, action.value))}
                  title={t(action.labelKey)}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span>{t(action.labelKey)}</span>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="status-actions" aria-label={t("post.manualStatus", { title: post.title })}>
            {statusActions.map((action) => {
              const Icon = action.icon;
              return (
                <button
                  key={action.value}
                  type="button"
                  className={post.review_status === action.value ? "status-action selected" : "status-action"}
                  onClick={() => onStatusChange(post.id, action.value)}
                  title={t(`status.${action.value}`)}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span>{t(`status.${action.value}`)}</span>
                </button>
              );
            })}
          </div>
        )}

        <div className="notes-row">
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            placeholder={t("post.notes")}
            rows={2}
          />
          <button
            className="icon-button"
            type="button"
            onClick={() => onNotesSave(post.id, notes)}
            title={t("post.saveNotes")}
          >
            <Save size={18} aria-hidden="true" />
          </button>
        </div>
      </div>
    </article>
  );
}

export default PostCard;
