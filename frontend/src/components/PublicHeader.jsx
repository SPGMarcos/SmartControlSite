import { ArrowRight, LogIn } from "lucide-react";
import { Link } from "react-router-dom";

import Logo from "./Logo.jsx";

export default function PublicHeader() {
  return (
    <header className="public-header">
      <Logo />
      <nav className="public-nav" aria-label="Principal">
        <a href="#servicos">Servicos</a>
        <a href="#portfolio">Portfolio</a>
        <a href="#planos">Planos</a>
        <a href="#processo">Processo</a>
      </nav>
      <div className="header-actions">
        <Link className="ghost-button" to="/login">
          <LogIn size={18} />
          Entrar
        </Link>
        <Link className="primary-button" to="/register">
          Comecar
          <ArrowRight size={18} />
        </Link>
      </div>
    </header>
  );
}
