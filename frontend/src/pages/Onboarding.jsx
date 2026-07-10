import { Check, Globe, Loader2, MapPin, Plus, RefreshCw, X } from "lucide-react";
import { useEffect, useState } from "react";
import {
  checkCrawlerLogin,
  detectFavoritesUrl,
  getCategoryPresets,
  importVisibleFavorites,
  openCrawlerLogin,
  patchConfig,
} from "../api.js";
import { useI18n } from "../i18n.jsx";

const SITE_OPTIONS = [
  { key: "rednote", icon: Globe },
  { key: "xiaohongshu", icon: MapPin },
];

const STEP_KEYS = ["region", "login", "categories", "fetch"];

function Onboarding({ onComplete }) {
  const { t, language } = useI18n();
  const [step, setStep] = useState(1);
  const [siteMode, setSiteMode] = useState("rednote");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  const [loginState, setLoginState] = useState("");

  const [presets, setPresets] = useState([]);
  const [selected, setSelected] = useState(() => new Set());
  const [customName, setCustomName] = useState("");
  const [customKeywords, setCustomKeywords] = useState("");
  const [customCategories, setCustomCategories] = useState([]);

  const [favoritesUrl, setFavoritesUrl] = useState("");
  const [detecting, setDetecting] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);

  const presetLabel = (preset) => (language === "zh" ? preset.label_zh : preset.label_en);

  useEffect(() => {
    if (step === 3 && presets.length === 0) {
      getCategoryPresets()
        .then((data) => {
          setPresets(data);
          setSelected(new Set(data.map((preset) => preset.slug)));
        })
        .catch((error) => setMessage(error.message));
    }
  }, [step, presets.length]);

  useEffect(() => {
    if (step === 4 && !favoritesUrl && !detecting) {
      runDetect();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  async function chooseRegionNext() {
    setBusy(true);
    setMessage("");
    try {
      await patchConfig({ site_mode: siteMode });
      setStep(2);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function openLogin() {
    setBusy(true);
    setMessage("");
    try {
      await openCrawlerLogin();
      setMessage(t("onboarding.loginOpened"));
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function checkLogin() {
    setBusy(true);
    setMessage("");
    try {
      const result = await checkCrawlerLogin();
      setLoginState(result.detected_state);
      if (result.detected_state !== "logged_in") {
        setMessage(t("onboarding.loginNotYet"));
      }
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  function toggleSlug(slug) {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(slug)) next.delete(slug);
      else next.add(slug);
      return next;
    });
  }

  function addCustom() {
    const name = customName.trim();
    if (!name) return;
    const keywords = customKeywords
      .split(/[,，\s]+/)
      .map((keyword) => keyword.trim())
      .filter(Boolean);
    setCustomCategories((current) => [...current, { name, keywords }]);
    setCustomName("");
    setCustomKeywords("");
  }

  function removeCustom(index) {
    setCustomCategories((current) => current.filter((_, i) => i !== index));
  }

  async function saveCategoriesNext() {
    setBusy(true);
    setMessage("");
    try {
      await patchConfig({
        selected_category_slugs: [...selected],
        custom_categories: customCategories,
      });
      setStep(4);
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function runDetect() {
    setDetecting(true);
    setMessage("");
    try {
      const result = await detectFavoritesUrl();
      if (result.favorites_url) setFavoritesUrl(result.favorites_url);
      else setMessage(result.message || t("onboarding.detectFailed"));
    } catch (error) {
      setMessage(error.message);
    } finally {
      setDetecting(false);
    }
  }

  async function startImport() {
    if (!favoritesUrl.trim()) {
      setMessage(t("onboarding.needUrl"));
      return;
    }
    setImporting(true);
    setMessage("");
    try {
      const result = await importVisibleFavorites({
        favoritesUrl: favoritesUrl.trim(),
        headless: true,
        initialReviewStatus: "unreviewed",
        // Bootstrap import must scroll the whole grid; the idle early-stop
        // ends it as soon as no new cards appear.
        maxScrolls: 100,
      });
      setImportResult(result);
      await patchConfig({ favorites_url: favoritesUrl.trim(), onboarding_completed: true });
    } catch (error) {
      setMessage(error.message);
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="onboarding">
      {importing ? (
        <div className="blocking-overlay" role="alert" aria-busy="true">
          <div className="blocking-overlay-card">
            <Loader2 className="spin" size={34} aria-hidden="true" />
            <span className="blocking-overlay-title">{t("onboarding.importing")}</span>
            <span className="blocking-overlay-hint">{t("onboarding.importingHint")}</span>
          </div>
        </div>
      ) : null}

      <div className="onboarding-card">
        <header className="onboarding-header">
          <strong>RedCache</strong>
          <span>{t("onboarding.welcome")}</span>
        </header>

        <ol className="onboarding-steps">
          {STEP_KEYS.map((key, index) => (
            <li key={key} className={step === index + 1 ? "active" : step > index + 1 ? "done" : ""}>
              <span className="step-dot">{step > index + 1 ? <Check size={14} /> : index + 1}</span>
              <span>{t(`onboarding.step.${key}`)}</span>
            </li>
          ))}
        </ol>

        <div className="onboarding-body">
          {step === 1 ? (
            <div className="onboarding-section">
              <h2>{t("onboarding.regionTitle")}</h2>
              <p className="onboarding-desc">{t("onboarding.regionDesc")}</p>
              <div className="region-options">
                {SITE_OPTIONS.map((option) => {
                  const Icon = option.icon;
                  return (
                    <button
                      key={option.key}
                      type="button"
                      className={siteMode === option.key ? "region-option selected" : "region-option"}
                      onClick={() => setSiteMode(option.key)}
                    >
                      <Icon size={22} aria-hidden="true" />
                      <strong>{t(`onboarding.site.${option.key}`)}</strong>
                      <span>{t(`onboarding.site.${option.key}.hint`)}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : null}

          {step === 2 ? (
            <div className="onboarding-section">
              <h2>{t("onboarding.loginTitle")}</h2>
              <p className="onboarding-desc">{t("onboarding.loginDesc")}</p>
              <div className="onboarding-actions-inline">
                <button type="button" className="secondary-button" onClick={openLogin} disabled={busy}>
                  {t("onboarding.openLogin")}
                </button>
                <button type="button" className="secondary-button" onClick={checkLogin} disabled={busy}>
                  <RefreshCw size={16} aria-hidden="true" />
                  {t("onboarding.checkLogin")}
                </button>
                {loginState === "logged_in" ? (
                  <span className="login-ok"><Check size={16} aria-hidden="true" /> {t("onboarding.loggedIn")}</span>
                ) : loginState ? (
                  <span className="login-pending">{loginState}</span>
                ) : null}
              </div>
            </div>
          ) : null}

          {step === 3 ? (
            <div className="onboarding-section">
              <h2>{t("onboarding.categoriesTitle")}</h2>
              <p className="onboarding-desc">{t("onboarding.categoriesDesc")}</p>
              <div className="category-chips">
                {presets.map((preset) => (
                  <button
                    key={preset.slug}
                    type="button"
                    className={selected.has(preset.slug) ? "category-chip selected" : "category-chip"}
                    onClick={() => toggleSlug(preset.slug)}
                  >
                    {presetLabel(preset)}
                  </button>
                ))}
              </div>

              <div className="custom-category">
                <h3>{t("onboarding.customTitle")}</h3>
                <p className="onboarding-desc">{t("onboarding.customDesc")}</p>
                <div className="custom-inputs">
                  <input
                    type="text"
                    value={customName}
                    placeholder={t("onboarding.customName")}
                    onChange={(event) => setCustomName(event.target.value)}
                  />
                  <input
                    type="text"
                    value={customKeywords}
                    placeholder={t("onboarding.customKeywords")}
                    onChange={(event) => setCustomKeywords(event.target.value)}
                  />
                  <button type="button" className="secondary-button" onClick={addCustom}>
                    <Plus size={16} aria-hidden="true" />
                    {t("onboarding.customAdd")}
                  </button>
                </div>
                {customCategories.length > 0 ? (
                  <div className="custom-list">
                    {customCategories.map((entry, index) => (
                      <span className="custom-tag" key={`${entry.name}-${index}`}>
                        {entry.name}
                        {entry.keywords.length ? ` (${entry.keywords.join(", ")})` : ` · ${t("onboarding.manualOnly")}`}
                        <button type="button" onClick={() => removeCustom(index)} aria-label="remove">
                          <X size={13} aria-hidden="true" />
                        </button>
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}

          {step === 4 ? (
            <div className="onboarding-section">
              <h2>{t("onboarding.fetchTitle")}</h2>
              <p className="onboarding-desc">{t("onboarding.fetchDesc")}</p>
              <label className="field onboarding-url">
                <span>{t("onboarding.favoritesUrl")}</span>
                <input
                  type="text"
                  value={favoritesUrl}
                  placeholder={t("onboarding.favoritesUrlPlaceholder")}
                  onChange={(event) => setFavoritesUrl(event.target.value)}
                />
              </label>
              <div className="onboarding-actions-inline">
                <button type="button" className="secondary-button" onClick={runDetect} disabled={detecting}>
                  {detecting ? <Loader2 className="spin" size={16} /> : <RefreshCw size={16} />}
                  {t("onboarding.redetect")}
                </button>
              </div>
              {importResult ? (
                <div className="notice">
                  {t("onboarding.importDone", {
                    imported: importResult.imported_count,
                    duplicate: importResult.duplicate_count,
                    scanned: importResult.scanned_count,
                  })}
                </div>
              ) : null}
            </div>
          ) : null}

          {message ? <div className="notice">{message}</div> : null}
        </div>

        <footer className="onboarding-footer">
          {step > 1 && !importResult ? (
            <button type="button" className="secondary-button" onClick={() => setStep(step - 1)} disabled={busy || importing}>
              {t("onboarding.back")}
            </button>
          ) : <span />}

          {step === 1 ? (
            <button type="button" className="primary-button" onClick={chooseRegionNext} disabled={busy}>
              {t("onboarding.next")}
            </button>
          ) : null}
          {step === 2 ? (
            <button
              type="button"
              className="primary-button"
              onClick={() => setStep(3)}
              disabled={loginState !== "logged_in"}
            >
              {t("onboarding.next")}
            </button>
          ) : null}
          {step === 3 ? (
            <button type="button" className="primary-button" onClick={saveCategoriesNext} disabled={busy}>
              {t("onboarding.next")}
            </button>
          ) : null}
          {step === 4 && !importResult ? (
            <button type="button" className="primary-button" onClick={startImport} disabled={importing || !favoritesUrl.trim()}>
              {t("onboarding.startImport")}
            </button>
          ) : null}
          {step === 4 && importResult ? (
            <button type="button" className="primary-button" onClick={onComplete}>
              {t("onboarding.enter")}
            </button>
          ) : null}
        </footer>
      </div>
    </div>
  );
}

export default Onboarding;
