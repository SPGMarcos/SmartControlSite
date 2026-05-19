import React from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import App from "./App.jsx";
import { AuthProvider } from "./contexts/AuthContext.jsx";
import { ThemeProvider } from "./contexts/ThemeContext.jsx";
import "./styles/global.css";

function restoreGitHubPagesRoute() {
  const redirect = window.location.search.match(/^\?\/(.*)/);
  if (!redirect) return;

  const route = redirect[1].replace(/~and~/g, "&");
  const searchIndex = route.indexOf("&");
  const pathname = searchIndex >= 0 ? route.slice(0, searchIndex) : route;
  const query = searchIndex >= 0 ? `?${route.slice(searchIndex + 1)}` : "";
  const basePath = import.meta.env.BASE_URL.replace(/\/$/, "");

  window.history.replaceState(null, "", `${basePath}/${pathname}${query}${window.location.hash}`);
}

restoreGitHubPagesRoute();

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <ThemeProvider>
        <AuthProvider>
          <App />
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>
);
