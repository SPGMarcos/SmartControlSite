import Logo from "./Logo.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

export default function AuthPanel({ title, subtitle, children }) {
  return (
    <main className="auth-page">
      <section className="auth-panel">
        <div className="auth-topbar">
          <Logo />
          <ThemeToggle compact />
        </div>
        <div className="auth-copy">
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        {children}
      </section>
      <section className="auth-side" aria-hidden="true">
        <div className="auth-metric">
          <span>Projetos ativos</span>
          <strong>24</strong>
        </div>
        <div className="auth-metric">
          <span>Disponibilidade</span>
          <strong>99.9%</strong>
        </div>
        <div className="auth-metric wide">
          <span>Seguranca</span>
          <strong>JWT, RBAC, Stripe Webhooks</strong>
        </div>
      </section>
    </main>
  );
}
