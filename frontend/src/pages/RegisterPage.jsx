import { CheckCircle2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import AuthPanel from "../components/AuthPanel.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { cleanText, isStrongEnoughPassword } from "../utils/security.js";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    company_name: "",
    email: "",
    phone: "",
    password: ""
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    if (!isStrongEnoughPassword(form.password)) {
      setError("Use uma senha com pelo menos 10 caracteres.");
      return;
    }
    setLoading(true);
    try {
      await register({
        ...form,
        first_name: cleanText(form.first_name),
        last_name: cleanText(form.last_name),
        company_name: cleanText(form.company_name),
        email: cleanText(form.email),
        phone: cleanText(form.phone)
      });
      navigate("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthPanel title="Comece seu projeto" subtitle="Crie sua area do cliente para acompanhar proposta, entrega e assinatura.">
      <form className="form two-columns" onSubmit={submit}>
        <label>
          Nome
          <input value={form.first_name} onChange={(event) => setForm({ ...form, first_name: event.target.value })} required />
        </label>
        <label>
          Sobrenome
          <input value={form.last_name} onChange={(event) => setForm({ ...form, last_name: event.target.value })} />
        </label>
        <label className="span-2">
          Empresa
          <input value={form.company_name} onChange={(event) => setForm({ ...form, company_name: event.target.value })} required />
        </label>
        <label>
          Email
          <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required />
        </label>
        <label>
          Telefone
          <input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
        </label>
        <label className="span-2">
          Senha
          <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required />
        </label>
        {error && <p className="form-error span-2">{error}</p>}
        <button className="primary-button full span-2" type="submit" disabled={loading}>
          {loading ? "Criando..." : "Criar conta"}
          <CheckCircle2 size={18} />
        </button>
      </form>
      <div className="auth-links">
        <Link to="/login">Ja tenho conta</Link>
      </div>
    </AuthPanel>
  );
}
