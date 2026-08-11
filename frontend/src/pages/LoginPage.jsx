import { ArrowRight } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import AuthPanel from "../components/AuthPanel.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { cleanText } from "../utils/security.js";

export default function LoginPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const redirectTarget = searchParams.get("redirect");

  const destinationFor = (user) => {
    if (redirectTarget?.startsWith("/")) {
      return redirectTarget.replace(/^\/register/, "/billing");
    }
    return user.role === "admin" ? "/admin" : "/dashboard";
  };

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const user = await login({ email: cleanText(form.email), password: form.password });
      navigate(destinationFor(user), { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthPanel title="Acesse sua conta" subtitle="Acompanhe projetos, pagamentos e solicitacoes em um ambiente seguro.">
      <form className="form" onSubmit={submit}>
        <label>
          Email
          <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
        </label>
        <label>
          Senha
          <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required />
        </label>
        {error && <p className="form-error">{error}</p>}
        <button className="primary-button full" type="submit" disabled={loading}>
          {loading ? "Entrando..." : "Entrar"}
          <ArrowRight size={18} />
        </button>
      </form>
      <div className="auth-links">
        <Link to="/reset-password">Recuperar senha</Link>
        <Link to={redirectTarget ? `/register${redirectTarget.includes("?") ? redirectTarget.slice(redirectTarget.indexOf("?")) : ""}` : "/register"}>
          Criar conta
        </Link>
      </div>
    </AuthPanel>
  );
}
