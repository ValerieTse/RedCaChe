import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import { CategoriesProvider } from "./CategoriesContext.jsx";
import { I18nProvider } from "./i18n.jsx";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <I18nProvider>
      <CategoriesProvider>
        <App />
      </CategoriesProvider>
    </I18nProvider>
  </React.StrictMode>,
);
