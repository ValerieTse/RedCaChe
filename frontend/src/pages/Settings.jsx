import { ExternalLink, Import, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import {
  API_BASE,
  getCrawlerSettings,
  importVisibleFavorites,
  openCrawlerLogin,
} from "../api.js";

function Settings() {
  const [loginUrl, setLoginUrl] = useState("");
  const [favoritesUrl, setFavoritesUrl] = useState("");
  const [profileDir, setProfileDir] = useState("");
  const [maxScrolls, setMaxScrolls] = useState(8);
  const [message, setMessage] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getCrawlerSettings()
      .then((settings) => {
        setLoginUrl(settings.login_url || "");
        setFavoritesUrl(settings.favorites_url || "");
        setProfileDir(settings.profile_dir || "");
        setMaxScrolls(settings.scroll_steps || 8);
      })
      .catch((error) => setMessage(error.message));
  }, []);

  async function handleOpenLogin() {
    setLoading(true);
    setMessage("");
    setReport(null);
    try {
      const result = await openCrawlerLogin(loginUrl);
      setProfileDir(result.profile_dir);
      setMessage(result.message);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleImportFavorites() {
    setLoading(true);
    setMessage("");
    setReport(null);
    try {
      const result = await importVisibleFavorites({
        favoritesUrl,
        maxScrolls: Number(maxScrolls) || 8,
      });
      setReport(result);
      if (result.stopped_reason) {
        setMessage(`Import stopped: ${result.stopped_reason}`);
      } else {
        setMessage("Visible import finished");
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Settings</h1>
          <p>Visible browser import</p>
        </div>
      </header>

      <div className="settings-grid">
        <label className="setting-field">
          <span>API base</span>
          <input value={API_BASE} readOnly />
        </label>
        <label className="setting-field">
          <span>Obsidian env</span>
          <input value="OBSIDIAN_VAULT_PATH" readOnly />
        </label>
        <label className="setting-field">
          <span>Backup env</span>
          <input value="BACKUP_ROOT" readOnly />
        </label>
        <label className="setting-field">
          <span>Persistent browser profile</span>
          <input value={profileDir} readOnly />
        </label>
        <label className="setting-field">
          <span>Xiaohongshu login URL</span>
          <input value={loginUrl} onChange={(event) => setLoginUrl(event.target.value)} />
        </label>
        <label className="setting-field">
          <span>Favorites/saved page URL</span>
          <input value={favoritesUrl} onChange={(event) => setFavoritesUrl(event.target.value)} />
        </label>
        <label className="setting-field">
          <span>Scroll passes</span>
          <input
            type="number"
            min="1"
            max="100"
            value={maxScrolls}
            onChange={(event) => setMaxScrolls(event.target.value)}
          />
        </label>
      </div>

      <div className="settings-actions">
        <button className="secondary-button" type="button" onClick={handleOpenLogin} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <ExternalLink size={18} aria-hidden="true" />}
          <span>Open Xiaohongshu login browser</span>
        </button>
        <button className="primary-button" type="button" onClick={handleImportFavorites} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Import size={18} aria-hidden="true" />}
          <span>Import visible saved posts</span>
        </button>
      </div>

      {message ? <div className="notice">{message}</div> : null}

      {report ? (
        <div className="report-grid">
          <ReportItem label="Import run" value={report.import_run_id} />
          <ReportItem label="Scanned" value={report.scanned_count} />
          <ReportItem label="Imported" value={report.imported_count} />
          <ReportItem label="Duplicates" value={report.duplicate_count} />
          <ReportItem label="Failed" value={report.failed_count} />
          <ReportItem label="Stopped reason" value={report.stopped_reason || "None"} />
        </div>
      ) : null}
    </section>
  );
}

function ReportItem({ label, value }) {
  return (
    <div className="report-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export default Settings;
