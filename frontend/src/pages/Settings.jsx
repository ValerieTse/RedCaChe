import { Bug, ExternalLink, Import, Loader2, Search, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import {
  API_BASE,
  checkCrawlerLogin,
  debugCrawlerProfile,
  getCrawlerSettings,
  inspectCrawlerPage,
  importVisibleFavorites,
  openCrawlerLogin,
} from "../api.js";
import { useI18n } from "../i18n.jsx";

function Settings() {
  const { t } = useI18n();
  const siteModeOptions = [
    { value: "rednote", label: t("settings.rednote") },
    { value: "xiaohongshu", label: t("settings.xiaohongshu") },
  ];
  const [selectedSiteMode, setSelectedSiteMode] = useState("rednote");
  const [activeSiteKey, setActiveSiteKey] = useState("rednote");
  const [activeSiteName, setActiveSiteName] = useState("RedNote");
  const [activeBaseUrl, setActiveBaseUrl] = useState("https://www.rednote.com");
  const [activeExploreUrl, setActiveExploreUrl] = useState("https://www.rednote.com/explore");
  const [favoritesUrl, setFavoritesUrl] = useState("");
  const [profileDir, setProfileDir] = useState("");
  const [backupRoot, setBackupRoot] = useState("");
  const [maxScrolls, setMaxScrolls] = useState(8);
  const [message, setMessage] = useState("");
  const [report, setReport] = useState(null);
  const [inspectionReport, setInspectionReport] = useState(null);
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
        setBackupRoot(settings.backup_root || "");
        setMaxScrolls(settings.scroll_steps || 8);
        setUseSystemChrome(Boolean(settings.use_system_chrome));
      })
      .catch((error) => setMessage(error.message));
  }, []);

  async function handleOpenLogin() {
    setLoading(true);
    setMessage("");
    setReport(null);
    setInspectionReport(null);
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
    setInspectionReport(null);
    try {
      const result = await checkCrawlerLogin();
      setLoginCheck(result);
      setActiveSiteKey(result.active_site_key || activeSiteKey);
      setActiveSiteName(result.active_site_display_name || activeSiteName);
      setActiveBaseUrl(result.active_base_url || activeBaseUrl);
      setProfileDir(result.profile_dir);
      setUseSystemChrome(Boolean(result.using_system_chrome));
      if (result.detected_state === "logged_in") {
        setMessage(t("settings.loginVerified"));
      } else {
        setMessage(t("settings.loginNotVerified", { state: result.detected_state }));
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
      setMessage(t("settings.profileLoaded"));
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
    setInspectionReport(null);
    try {
      const result = await importVisibleFavorites({
        favoritesUrl,
        maxScrolls: Number(maxScrolls) || 8,
        initialReviewStatus: "keep",
      });
      setReport(result);
      if (result.stopped_reason) {
        setMessage(t("settings.importStopped", { reason: result.stopped_reason }));
      } else {
        setMessage(t("settings.importFinished"));
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleInspectPage() {
    setLoading(true);
    setMessage("");
    setReport(null);
    setInspectionReport(null);
    try {
      const result = await inspectCrawlerPage({
        url: favoritesUrl,
        maxScrolls: Number(maxScrolls) || 2,
      });
      setInspectionReport(result);
      setMessage(t("settings.inspectFinished", { count: result.candidate_note_links_count }));
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
          <h1>{t("settings.title")}</h1>
          <p>{t("settings.subtitle")}</p>
        </div>
      </header>

      <div className="settings-grid">
        <label className="setting-field">
          <span>{t("settings.siteMode")}</span>
          <select value={selectedSiteMode} onChange={(event) => setSelectedSiteMode(event.target.value)}>
            {siteModeOptions.map((option) => (
              <option value={option.value} key={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="setting-field">
          <span>{t("settings.apiBase")}</span>
          <input value={API_BASE} readOnly />
        </label>
        <label className="setting-field">
          <span>{t("settings.obsidianEnv")}</span>
          <input value="OBSIDIAN_VAULT_PATH" readOnly />
        </label>
        <label className="setting-field">
          <span>{t("settings.backupEnv")}</span>
          <input value={backupRoot || "BACKUP_ROOT"} readOnly />
        </label>
        <label className="setting-field">
          <span>{t("settings.activeBaseUrl")}</span>
          <input value={activeBaseUrl} readOnly />
        </label>
        <label className="setting-field">
          <span>{t("settings.activeExploreUrl")}</span>
          <input value={activeExploreUrl} readOnly />
        </label>
        <label className="setting-field">
          <span>{t("settings.profile")}</span>
          <input value={profileDir} readOnly />
        </label>
        <label className="setting-field">
          <span>{t("settings.systemChrome")}</span>
          <input value={useSystemChrome ? t("settings.systemChromeOn") : t("settings.bundledChromium")} readOnly />
        </label>
        <label className="setting-field">
          <span>{t("settings.favoritesUrl")}</span>
          <input value={favoritesUrl} onChange={(event) => setFavoritesUrl(event.target.value)} />
        </label>
        <label className="setting-field">
          <span>{t("settings.scrollPasses")}</span>
          <input
            type="number"
            min="1"
            max="500"
            value={maxScrolls}
            onChange={(event) => setMaxScrolls(event.target.value)}
          />
        </label>
      </div>

      {selectedSiteMode !== activeSiteKey ? (
        <div className="warning-panel">
          {t("settings.modeWarning", { site: activeSiteName, mode: selectedSiteMode })}
        </div>
      ) : null}

      <div className="instructions-panel">
        <ol>
          <li>{t("settings.step1", { site: activeSiteName })}</li>
          <li>{t("settings.step2")}</li>
          <li>{t("settings.step3", { url: activeExploreUrl })}</li>
          <li>{t("settings.step4")}</li>
          <li>{t("settings.step5")}</li>
          <li>{t("settings.step6")}</li>
          <li>{t("settings.step7")}</li>
        </ol>
      </div>

      <div className="settings-actions">
        <button className="secondary-button" type="button" onClick={handleOpenLogin} disabled={loading || selectedSiteMode !== activeSiteKey}>
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <ExternalLink size={18} aria-hidden="true" />}
          <span>{t("settings.openLogin", { site: activeSiteName })}</span>
        </button>
        <button className="secondary-button" type="button" onClick={handleCheckLogin} disabled={loading || selectedSiteMode !== activeSiteKey}>
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <ShieldCheck size={18} aria-hidden="true" />}
          <span>{t("settings.checkLogin")}</span>
        </button>
        <button className="secondary-button" type="button" onClick={handleDebugProfile} disabled={loading || selectedSiteMode !== activeSiteKey}>
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Bug size={18} aria-hidden="true" />}
          <span>{t("settings.debugProfile")}</span>
        </button>
        <button
          className="secondary-button"
          type="button"
          onClick={handleInspectPage}
          disabled={loading || selectedSiteMode !== activeSiteKey || !favoritesUrl.trim()}
        >
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Search size={18} aria-hidden="true" />}
          <span>{t("settings.inspectPage")}</span>
        </button>
        <button
          className="primary-button"
          type="button"
          onClick={handleImportFavorites}
          disabled={loading || selectedSiteMode !== activeSiteKey || loginCheck?.detected_state !== "logged_in"}
        >
          {loading ? <Loader2 className="spin" size={18} aria-hidden="true" /> : <Import size={18} aria-hidden="true" />}
          <span>{t("settings.import")}</span>
        </button>
      </div>

      {message ? <div className="notice">{message}</div> : null}

      {loginCheck && loginCheck.detected_state !== "logged_in" ? (
        <div className="warning-panel">{t("settings.loginWarning")}</div>
      ) : null}

      {loginCheck ? (
        <div className="report-grid">
          <ReportItem label={t("report.activeSite")} value={loginCheck.active_site_display_name || activeSiteName} />
          <ReportItem label={t("report.loginState")} value={loginCheck.detected_state} />
          <ReportItem label={t("report.currentUrl")} value={loginCheck.current_url} />
          <ReportItem label={t("report.pageTitle")} value={loginCheck.page_title || t("common.untitled")} />
          <ReportItem label={t("report.screenshot")} value={loginCheck.screenshot_path || t("common.none")} />
          <ReportItem label={t("report.domainCookies")} value={loginCheck.cookies_count_for_domain ?? t("common.unknown")} />
          <ReportItem label={t("report.storageKeys")} value={loginCheck.local_storage_keys_count ?? t("common.unknown")} />
        </div>
      ) : null}

      {profileDebug ? (
        <div className="report-grid">
          <ReportItem label={t("report.activeSite")} value={profileDebug.active_site_display_name || activeSiteName} />
          <ReportItem label={t("report.profileExists")} value={profileDebug.profile_dir_exists ? t("common.yes") : t("common.no")} />
          <ReportItem label={t("report.profileSize")} value={`${profileDebug.profile_dir_size_bytes} bytes`} />
          <ReportItem label={t("report.chromeEnabled")} value={profileDebug.system_chrome_enabled ? t("common.yes") : t("common.no")} />
          <ReportItem label={t("report.chromeUsing")} value={profileDebug.using_system_chrome ? t("common.yes") : t("common.no")} />
          <ReportItem label={t("report.chromeFallback")} value={profileDebug.launch_fallback_reason || t("common.none")} />
          <ReportItem label={t("report.lastLaunch")} value={profileDebug.last_browser_launch_timestamp || t("common.none")} />
        </div>
      ) : null}

      {inspectionReport ? (
        <div className="report-grid">
          <ReportItem label={t("report.inspectionState")} value={inspectionReport.detected_state} />
          <ReportItem label={t("report.currentUrl")} value={inspectionReport.current_url} />
          <ReportItem label={t("report.pageTitle")} value={inspectionReport.page_title || t("common.untitled")} />
          <ReportItem label={t("report.totalLinks")} value={inspectionReport.total_links_count} />
          <ReportItem label={t("report.candidateLinks")} value={inspectionReport.candidate_note_links_count} />
          <ReportItem label={t("report.candidateCards")} value={inspectionReport.candidate_card_count} />
          <ReportItem label={t("report.strategies")} value={formatStrategyResults(inspectionReport.selector_strategy_results, t("common.none"))} />
          <ReportItem label={t("report.screenshots")} value={formatList(inspectionReport.debug_screenshot_paths, t("common.none"))} />
          <ReportItem label={t("report.html")} value={inspectionReport.debug_html_path || t("common.none")} />
          <ReportItem label={t("report.textDump")} value={inspectionReport.debug_text_path || t("common.none")} />
          <ReportItem label={t("report.candidateSamples")} value={formatList(inspectionReport.candidate_note_links, t("common.none"))} />
        </div>
      ) : null}

      {report ? (
        <div className="report-grid">
          <ReportItem label={t("report.importRun")} value={report.import_run_id} />
          <ReportItem label={t("report.scanned")} value={report.scanned_count} />
          <ReportItem label={t("report.imported")} value={report.imported_count} />
          <ReportItem label={t("report.duplicates")} value={report.duplicate_count} />
          <ReportItem label={t("report.failed")} value={report.failed_count} />
          <ReportItem label={t("report.stoppedReason")} value={report.stopped_reason || t("common.none")} />
          <ReportItem label={t("report.expectedDomain")} value={report.expected_domain || t("common.none")} />
          <ReportItem label={t("report.receivedUrl")} value={report.received_url || t("common.none")} />
        </div>
      ) : null}

    </section>
  );
}

function formatList(values = [], emptyLabel = "None") {
  if (!values.length) return emptyLabel;
  return values.slice(0, 10).join("\n");
}

function formatStrategyResults(results = {}, emptyLabel = "None") {
  const entries = Object.entries(results);
  if (!entries.length) return emptyLabel;
  return entries.map(([key, value]) => `${key}: ${String(value)}`).join("\n");
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
