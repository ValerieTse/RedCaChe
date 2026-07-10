import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { getCategories } from "./api.js";
import { useI18n } from "./i18n.jsx";

const CategoriesContext = createContext(null);

export function CategoriesProvider({ children }) {
  const { language } = useI18n();
  const [categories, setCategories] = useState([]);

  const reload = useCallback(async () => {
    try {
      setCategories(await getCategories());
    } catch {
      // Categories are non-critical for rendering; ignore fetch failures.
    }
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  const labelFor = useCallback(
    (slug) => {
      const match = categories.find((category) => category.slug === slug);
      if (!match) return slug;
      return language === "zh" ? match.label_zh : match.label_en;
    },
    [categories, language],
  );

  return (
    <CategoriesContext.Provider value={{ categories, labelFor, reload }}>
      {children}
    </CategoriesContext.Provider>
  );
}

export function useCategories() {
  const ctx = useContext(CategoriesContext);
  if (!ctx) throw new Error("useCategories must be used within CategoriesProvider");
  return ctx;
}
