import { Moon, Sun } from "lucide-react";

import { useTheme } from "../hooks/useTheme.js";

export default function ThemeToggle({ compact = false }) {
  const { isDark, toggleTheme } = useTheme();
  return (
    <button
      className={`theme-toggle ${compact ? "theme-toggle-compact" : ""}`}
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? "Ativar tema claro" : "Ativar tema escuro"}
      title={isDark ? "Tema claro" : "Tema escuro"}
    >
      <span className="theme-toggle-track">
        <Sun className="theme-icon sun-icon" size={16} />
        <Moon className="theme-icon moon-icon" size={16} />
      </span>
      {!compact && <span>{isDark ? "Claro" : "Escuro"}</span>}
    </button>
  );
}
