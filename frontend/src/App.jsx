import {
  Archive,
  Database,
  LayoutDashboard,
  Leaf,
  Settings as SettingsIcon,
  Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import DailyReview from "./pages/DailyReview.jsx";
import Evergreen from "./pages/Evergreen.jsx";
import BackupLibrary from "./pages/BackupLibrary.jsx";
import Settings from "./pages/Settings.jsx";

const tabs = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard, component: Dashboard },
  { id: "daily", label: "Daily Review", icon: Sparkles, component: DailyReview },
  { id: "evergreen", label: "Evergreen", icon: Leaf, component: Evergreen },
  { id: "backups", label: "Backups", icon: Archive, component: BackupLibrary },
  { id: "settings", label: "Settings", icon: SettingsIcon, component: Settings },
];

function App() {
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
            <span>Local review</span>
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
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>
      <main className="main-panel">
        <ActivePage />
      </main>
    </div>
  );
}

function getTabFromHash() {
  const hash = window.location.hash.replace("#", "") || "dashboard";
  return tabs.some((tab) => tab.id === hash) ? hash : "dashboard";
}

export default App;
