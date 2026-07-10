import { RotateCcw } from "lucide-react";
import { useCategories } from "../CategoriesContext.jsx";
import { useI18n } from "../i18n.jsx";

function FilterBar({ category, onCategoryChange, onReset }) {
  const { t } = useI18n();
  const { categories, labelFor } = useCategories();

  return (
    <div className="filter-bar">
      <label className="field">
        <span>{t("filter.category")}</span>
        <select value={category} onChange={(event) => onCategoryChange(event.target.value)}>
          <option value="">{t("filter.all")}</option>
          {categories.map((item) => (
            <option value={item.slug} key={item.slug}>
              {labelFor(item.slug)}
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
