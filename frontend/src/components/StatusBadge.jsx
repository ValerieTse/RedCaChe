const statusLabels = {
  unreviewed: "Unreviewed",
  keep: "Keep",
  remove_from_xhs: "Remove",
  evergreen: "Evergreen",
  archived: "Archived",
};

function StatusBadge({ status }) {
  return <span className={`status-badge status-${status}`}>{statusLabels[status] || status}</span>;
}

export default StatusBadge;
