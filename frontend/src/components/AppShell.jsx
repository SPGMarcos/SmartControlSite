import { CreditCard, LayoutDashboard, LogOut, Shield, ShieldCheck, UserRound } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth.js";
import Logo from "./Logo.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

export default function AppShell({ children }) {
  const { user, isAdmin, isUserPreviewMode, exitUserPreviewMode, logout } = useAuth();
  const navigate = useNavigate();

  const returnToAdmin = () => {
    exitUserPreviewMode();
    navigate("/admin");
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-top">
          <Logo to="/" />
          <ThemeToggle compact />
        </div>
        <nav className="side-nav" aria-label="Aplicacao">
          <NavLink to="/dashboard">
            <LayoutDashboard size={18} />
            Cliente
          </NavLink>
          <NavLink to="/billing">
            <CreditCard size={18} />
            Billing
          </NavLink>
          {isAdmin && !isUserPreviewMode && (
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
      <main className="app-main">
        {isUserPreviewMode && (
          <section className="user-preview-banner" role="status" aria-live="polite">
            <ShieldCheck size={19} />
            <strong>Modo de visualização do usuário — Você está conectado como administrador.</strong>
            <button className="secondary-button" type="button" onClick={returnToAdmin}>
              Voltar para Administração
            </button>
          </section>
        )}
        {children}
      </main>
    </div>
  );
}
