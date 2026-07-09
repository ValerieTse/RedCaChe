import { Bug, ExternalLink, Import, Loader2, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import {
  API_BASE,
  checkCrawlerLogin,
  debugCrawlerProfile,
  getCrawlerSettings,
  importVisibleFavorites,
  openCrawlerLogin,
} from "../api.js";

const siteModeOptions = [
  { value: "rednote", label: "RedNote / Overseas" },
  { value: "xiaohongshu", label: "Xiaohongshu / Mainland China" },
];

function Settings() {
  const [selectedSiteMode, setSelectedSiteMode] = useState("rednote");
  const [activeSiteKey, setActiveSiteKey] = useState("rednote");
  const [activeSiteName, setActiveSiteName] = useState("RedNote");
  const [activeBaseUrl, setActiveBaseUrl] = useState("https://www.rednote.com");
  const [activeExploreUrl, setActiveExploreUrl] = useState("https://www.rednote.com/explore");
  const [favoritesUrl, setFavoritesUrl] = useState("");
  const [profileDir, setProfileDir] = useState("");
  const [maxScrolls, setMaxScrolls] = useState(8);
  const [message, setMessage] = useState("");
  const [report, setReport] = useState(null);
  const [loginCheck, setLoginCheck] = useState(null);
  const [profileDebug, setProfileDebug] = useState(null);
  const [useSystemChrome, setUseSystemChrome] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getCrawlerSettings()
      .then((settings) => {
        setSelectedSiteMode(settings.active_site_key || "rednote");
        setActiveSiteKey(settings.active_site_key || "rednote");
        setActiveSiteName(settings.active_site_display_name || "RedNote");
        setActiveBaseUrl(settings.active_base_url || "https://www.rednote.com");
        setActiveExploreUrl(settings.active_explore_url || "https://www.rednote.com/explore");
        setFavoritesUrl(settings.favorites_url || "");
        setProfileDir(settings.profile_dir || "");
        setMaxScrolls(settings.scroll_steps || 8);
        setUseSystemChrome(Boolean(settings.use_system_chrome));
      })
      .catch((error) => setMessage(error.message));
  }, []);

  async function handleOpenLogin() {
    setLoading(true);
    setMessage("");
    setReport(null);
    try {
      const result = await openCrawlerLogin();
      setActiveSiteKey(result.active_site_key || activeSiteKey);
      setActiveSiteName(result.active_site_display_name || activeSiteName);
      setActiveBaseUrl(result.active_base_url || activeBaseUrl);
      setProfileDir(result.profile_dir);
      setUseSystemChrome(Boolean(result.using_system_chrome));
      setMessage(result.message);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCheckLogin() {
    setLoading(true);
    setMessage("");
    setReport(null);
    try {
      const result = await checkCrawlerLogin();
      setLoginCheck(result);
      setActiveSiteKey(result.active_site_key || activeSiteKey);
      setActiveSiteName(result.active_site_display_name || activeSiteName);
      setActiveBaseUrl(result.active_base_url || activeBaseUrl);
      setProfileDir(result.profile_dir);
      setUseSystemChrome(Boolean(result.using_system_chrome));
      if (result.detected_state === "logged_in") {
        setMessage("Login status looks verified.");
      } else {
        setMessage(`Login is not verified: ${result.detected_state}`);
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleDebugProfile() {
    setLoading(true);
    setMessage("");
    try {
      const result = await debugCrawlerProfile();
      setProfileDebug(result);
      setActiveSiteKey(result.active_site_key || activeSiteKey);
      setActiveSiteName(result.active_site_display_name || activeSiteName);
      setActiveBaseUrl(result.active_base_url || activeBaseUrl);
      setProfileDir(result.profile_dir);
      setUseSystemChrome(Boolean(result.using_system_chrome));
      setMessage("Profile debug loaded.");
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
          <span>Site mode</span>
          <select value={selectedSiteMode} onChange={(event) => setSelectedSiteMode(event.target.value)}>
            {siteModeOptions.map((option) => (
              <option value={option.value} key={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
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
          <span>Active base URL</span>
          <input value={activeBaseUrl} readOnly />
        </label>
        <label className="setting-field">
          <span>Active explore URL</span>
          <input value={activeExploreUrl} readOnly />
        </label>
        <label className="setting-field">
          <span>Persistent browser profile</span>
          <input value={profileDir} readOnly />
        </label>
        <label className="setting-field">
          <span>System Chrome</span>
          <input value={useSystemChrome ? "Enabled or in use" : "Bundled Chromium"} readOnly />
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

      {selectedSiteMode !== activeSiteKey ? (
        <div className="warning-panel">
          Backend is running in {activeSiteName} mode. Set XHS_SITE_MODE={selectedSiteMode} and restart the backend before using this selection.
        </div>
      ) : null}

      <div className="instructions-panel">
        <ol>
          <li>Open the {activeSiteName} login browser.</li>
          <li>Log in manually in the visible browser.</li>
          <li>After login, go to {activeExploreUrl}.</li>
          <li>Check login status before importing.</li>
          <li>Only import when status is logged_in.</li>
          <li>Paste the actual saved/favorites URL copied from the logged-in browser.</li>
          <li>Handle CAPTCHA or challenges manually; RedCache will not bypass them.</li>
        </ol>
      </div>

      <div className="settings-actions">
        <button className="secondary-button" type="button" onClick={handleOpenLogin} disabled={loading || selectedSiteMode !== activeSiteKey}>
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <ExternalLink size={18} aria-hidden="true" />}
          <span>Open {activeSiteName} login browser</span>
        </button>
        <button className="secondary-button" type="button" onClick={handleCheckLogin} disabled={loading || selectedSiteMode !== activeSiteKey}>
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <ShieldCheck size={18} aria-hidden="true" />}
          <span>Check login status</span>
        </button>
        <button className="secondary-button" type="button" onClick={handleDebugProfile} disabled={loading || selectedSiteMode !== activeSiteKey}>
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Bug size={18} aria-hidden="true" />}
          <span>Debug browser profile</span>
        </button>
        <button
          className="primary-button"
          type="button"
          onClick={handleImportFavorites}
          disabled={loading || selectedSiteMode !== activeSiteKey || loginCheck?.detected_state !== "logged_in"}
        >
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Import size={18} aria-hidden="true" />}
          <span>Import visible saved posts</span>
        </button>
      </div>

      {message ? <div className="notice">{message}</div> : null}

      {loginCheck && loginCheck.detected_state !== "logged_in" ? (
        <div className="warning-panel">Login is not persistent or not verified yet. Do not import until status is logged_in.</div>
      ) : null}

      {loginCheck ? (
        <div className="report-grid">
          <ReportItem label="Active site" value={loginCheck.active_site_display_name || activeSiteName} />
          <ReportItem label="Login state" value={loginCheck.detected_state} />
          <ReportItem label="Current URL" value={loginCheck.current_url} />
          <ReportItem label="Page title" value={loginCheck.page_title || "Untitled"} />
          <ReportItem label="Screenshot" value={loginCheck.screenshot_path || "None"} />
          <ReportItem label="Domain cookies" value={loginCheck.cookies_count_for_domain ?? "Unknown"} />
          <ReportItem label="Local storage keys" value={loginCheck.local_storage_keys_count ?? "Unknown"} />
        </div>
      ) : null}

      {profileDebug ? (
        <div className="report-grid">
          <ReportItem label="Active site" value={profileDebug.active_site_display_name || activeSiteName} />
          <ReportItem label="Profile exists" value={profileDebug.profile_dir_exists ? "Yes" : "No"} />
          <ReportItem label="Profile size" value={`${profileDebug.profile_dir_size_bytes} bytes`} />
          <ReportItem label="System Chrome enabled" value={profileDebug.system_chrome_enabled ? "Yes" : "No"} />
          <ReportItem label="Using system Chrome" value={profileDebug.using_system_chrome ? "Yes" : "No"} />
          <ReportItem label="Chrome fallback" value={profileDebug.launch_fallback_reason || "None"} />
          <ReportItem label="Last launch" value={profileDebug.last_browser_launch_timestamp || "None"} />
        </div>
      ) : null}

      {report ? (
        <div className="report-grid">
          <ReportItem label="Import run" value={report.import_run_id} />
          <ReportItem label="Scanned" value={report.scanned_count} />
          <ReportItem label="Imported" value={report.imported_count} />
          <ReportItem label="Duplicates" value={report.duplicate_count} />
          <ReportItem label="Failed" value={report.failed_count} />
          <ReportItem label="Stopped reason" value={report.stopped_reason || "None"} />
          <ReportItem label="Expected domain" value={report.expected_domain || "None"} />
          <ReportItem label="Received URL" value={report.received_url || "None"} />
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
