import { LayoutDashboard, LogOut, Shield, UserRound } from "lucide-react";
import { NavLink } from "react-router-dom";

import { useAuth } from "../hooks/useAuth.js";
import Logo from "./Logo.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

export default function AppShell({ children }) {
  const { user, isAdmin, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-top">
          <Logo to="/dashboard" />
          <ThemeToggle compact />
        </div>
        <nav className="side-nav" aria-label="Aplicacao">
          <NavLink to="/dashboard">
            <LayoutDashboard size={18} />
            Cliente
          </NavLink>
          {isAdmin && (
            <NavLink to="/admin">
              <Shield size={18} />
              Admin
            </NavLink>
          )}
        </nav>
        <div className="sidebar-user">
          <UserRound size={18} />
          <div>
            <strong>{user?.first_name || "Usuario"}</strong>
            <span>{user?.email}</span>
          </div>
        </div>
        <button className="ghost-button full" type="button" onClick={logout}>
          <LogOut size={18} />
          Sair
        </button>
      </aside>
      <main className="app-main">{children}</main>
    </div>
  );
}
