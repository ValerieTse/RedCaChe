import { useI18n } from "../i18n.jsx";

function StatusBadge({ status }) {
  const { t } = useI18n();
  return <span className={`status-badge status-${status}`}>{t(`status.${status}`)}</span>;
}

export default StatusBadge;
