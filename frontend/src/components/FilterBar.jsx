import { Filter, RotateCcw, Search } from "lucide-react";

const categories = ["", "Beauty", "Fashion", "Fitness", "Work", "Study", "Life", "Food", "Travel", "Other"];
const statuses = ["", "unreviewed", "keep", "remove_from_xhs", "evergreen", "archived"];

function FilterBar({ category, status, onCategoryChange, onStatusChange, onReset }) {
  return (
    <div className="filter-bar">
      <div className="filter-title">
        <Filter size={18} aria-hidden="true" />
        <span>Filters</span>
      </div>
      <label className="field">
        <span>Category</span>
        <select value={category} onChange={(event) => onCategoryChange(event.target.value)}>
          {categories.map((item) => (
            <option value={item} key={item || "all-categories"}>
              {item || "All"}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Status</span>
        <select value={status} onChange={(event) => onStatusChange(event.target.value)}>
          {statuses.map((item) => (
            <option value={item} key={item || "all-statuses"}>
              {item || "All"}
            </option>
          ))}
        </select>
      </label>
      <button className="icon-button" type="button" onClick={onReset} title="Reset filters">
        <RotateCcw size={18} aria-hidden="true" />
      </button>
      <Search className="filter-endcap" size={18} aria-hidden="true" />
    </div>
  );
}

export default FilterBar;
