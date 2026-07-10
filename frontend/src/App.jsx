import {
  Archive,
  ClipboardCheck,
  Database,
  LayoutDashboard,
  Languages,
  Leaf,
  Settings as SettingsIcon,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useI18n } from "./i18n.jsx";
import Archived from "./pages/Archived.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import DailyReview from "./pages/DailyReview.jsx";
import Evergreen from "./pages/Evergreen.jsx";
import RemoveCheck from "./pages/RemoveCheck.jsx";
import Settings from "./pages/Settings.jsx";

const tabs = [
  { id: "daily", labelKey: "nav.daily", icon: Sparkles, component: DailyReview },
  { id: "library", labelKey: "nav.library", icon: LayoutDashboard, component: Dashboard },
  { id: "evergreen", labelKey: "nav.evergreen", icon: Leaf, component: Evergreen },
  { id: "remove-check", labelKey: "nav.removeCheck", icon: ClipboardCheck, component: RemoveCheck },
  { id: "archived", labelKey: "nav.archived", icon: Archive, component: Archived },
  { id: "settings", labelKey: "nav.settings", icon: SettingsIcon, component: Settings },
];

function App() {
  const { language, setLanguage, t } = useI18n();
  const [activeTab, setActiveTab] = useState(getTabFromHash);
  const ActivePage = tabs.find((tab) => tab.id === activeTab).component;

  useEffect(() => {
    const syncHash = () => setActiveTab(getTabFromHash());
    window.addEventListener("hashchange", syncHash);
    return () => window.removeEventListener("hashchange", syncHash);
  }, []);

  function navigate(tabId) {
    window.location.hash = tabId;
    setActiveTab(tabId);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <Database size={24} aria-hidden="true" />
          <div>
            <strong>RedCache</strong>
            <span>{t("app.tagline")}</span>
          </div>
        </div>
        <nav className="nav-list" aria-label="Primary">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                className={tab.id === activeTab ? "nav-item active" : "nav-item"}
                type="button"
                onClick={() => navigate(tab.id)}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{t(tab.labelKey)}</span>
              </button>
            );
          })}
        </nav>
        <div className="sidebar-language">
          <Languages size={17} aria-hidden="true" />
          <span className="language-label">{t("language.label")}</span>
          <div className="language-switch" role="group" aria-label={t("language.label")}>
            <button
              type="button"
              className={language === "zh" ? "active" : ""}
              onClick={() => setLanguage("zh")}
            >
              {t("language.zh")}
            </button>
            <button
              type="button"
              className={language === "en" ? "active" : ""}
              onClick={() => setLanguage("en")}
            >
              {t("language.en")}
            </button>
          </div>
        </div>
      </aside>
      <main className="main-panel">
        <ActivePage />
      </main>
    </div>
  );
}

function getTabFromHash() {
  const hash = window.location.hash.replace("#", "") || "daily";
  if (hash === "dashboard") return "library";
  if (hash === "backups") return "settings";
  return tabs.some((tab) => tab.id === hash) ? hash : "daily";
}

export default App;
