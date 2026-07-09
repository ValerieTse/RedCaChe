import { Archive, FolderLock, Image, ScrollText } from "lucide-react";

const backupRows = [
  { label: "Raw backups", path: "data/backups/raw_html", icon: ScrollText },
  { label: "Screenshots", path: "data/backups/screenshots", icon: Image },
  { label: "Images", path: "data/backups/images", icon: FolderLock },
];

function BackupLibrary() {
  return (
    <section className="page">
      <header className="page-header">
        <div>
          <h1>Backup Library</h1>
          <p>Obsidian sync off</p>
        </div>
        <Archive size={28} aria-hidden="true" />
      </header>

      <div className="backup-list">
        {backupRows.map((row) => {
          const Icon = row.icon;
          return (
            <div className="backup-row" key={row.path}>
              <Icon size={20} aria-hidden="true" />
              <div>
                <strong>{row.label}</strong>
                <span>{row.path}</span>
              </div>
              <span className="status-badge status-archived">Local</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default BackupLibrary;
