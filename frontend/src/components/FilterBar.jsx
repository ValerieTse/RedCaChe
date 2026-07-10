import { RotateCcw } from "lucide-react";
import { POST_CATEGORIES } from "../categories.js";
import { useI18n } from "../i18n.jsx";

const categories = ["", ...POST_CATEGORIES];

function FilterBar({ category, onCategoryChange, onReset }) {
  const { t } = useI18n();

  return (
    <div className="filter-bar">
      <label className="field">
        <span>{t("filter.category")}</span>
        <select value={category} onChange={(event) => onCategoryChange(event.target.value)}>
          {categories.map((item) => (
            <option value={item} key={item || "all-categories"}>
              {item ? t(`category.${item}`) : t("filter.all")}
            </option>
          ))}
        </select>
      </label>
      <button className="icon-button" type="button" onClick={onReset} title={t("filter.reset")}>
        <RotateCcw size={18} aria-hidden="true" />
      </button>
    </div>
  );
}

export default FilterBar;
