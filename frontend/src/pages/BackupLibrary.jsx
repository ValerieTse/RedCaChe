import { Archive, ExternalLink, FolderLock, Image, Search, ScrollText } from "lucide-react";
import { useEffect, useState } from "react";
import { openPostSource, searchBackupPosts } from "../api.js";
import { useI18n } from "../i18n.jsx";
import { resolvePostOpenUrl } from "../components/postLinks.js";

const backupRows = [
  { labelKey: "backup.raw", path: "data/backups/raw_html", icon: ScrollText },
  { labelKey: "backup.screenshots", path: "data/backups/screenshots", icon: Image },
  { labelKey: "backup.images", path: "data/backups/images", icon: FolderLock },
];

function BackupLibrary() {
  const { t } = useI18n();
  const [query, setQuery] = useState("");
  const [posts, setPosts] = useState([]);
  const [message, setMessage] = useState("");
  const [openingPostId, setOpeningPostId] = useState(null);

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      try {
        const data = await searchBackupPosts(query);
        setPosts(data.posts);
        setMessage("");
      } catch (error) {
        setMessage(error.message);
      }
    }, 180);
    return () => window.clearTimeout(timer);
  }, [query]);

  async function handleOpenSource(postId) {
    setOpeningPostId(postId);
    try {
      await openPostSource(postId);
      setMessage(t("post.openedInBrowser"));
    } catch (error) {
      setMessage(error.message);
    } finally {
      setOpeningPostId(null);
    }
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>{t("backup.title")}</h1>
          <p>{t("backup.subtitle")}</p>
        </div>
        <Archive size={28} aria-hidden="true" />
      </header>

      <label className="backup-search">
        <Search size={18} aria-hidden="true" />
        <span className="sr-only">{t("backup.search")}</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={t("backup.searchPlaceholder")}
        />
      </label>

      {message ? <div className="notice">{message}</div> : null}

      <div className="backup-results">
        {posts.map((post) => {
          const openUrl = resolvePostOpenUrl(post);
          return (
            <div className="backup-post-row" key={post.id}>
              <div>
                <strong>{post.title}</strong>
                <span>{post.author || t("common.unknown")} · {post.note_id}</span>
              </div>
              <span className="status-badge status-archived">{t(`status.${post.review_status}`)}</span>
              {openUrl ? (
                <button
                  type="button"
                  className="link-button"
                  onClick={() => handleOpenSource(post.id)}
                  disabled={openingPostId === post.id}
                  title={t("post.openSource")}
                >
                  <ExternalLink size={17} aria-hidden="true" />
                  <span className="sr-only">
                    {openingPostId === post.id ? t("common.loading") : t("post.openSource")}
                  </span>
                </button>
              ) : null}
            </div>
          );
        })}
      </div>

      <div className="backup-list">
        {backupRows.map((row) => {
          const Icon = row.icon;
          return (
            <div className="backup-row" key={row.path}>
              <Icon size={20} aria-hidden="true" />
              <div>
                <strong>{t(row.labelKey)}</strong>
                <span>{row.path}</span>
              </div>
              <span className="status-badge status-archived">{t("backup.local")}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default BackupLibrary;
