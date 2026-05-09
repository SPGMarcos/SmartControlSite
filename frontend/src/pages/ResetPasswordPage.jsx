import { MailCheck } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import AuthPanel from "../components/AuthPanel.jsx";
import { confirmPasswordReset, requestPasswordReset } from "../services/authService.js";
import { cleanText, isStrongEnoughPassword } from "../utils/security.js";

export default function ResetPasswordPage() {
  const [params] = useSearchParams();
  const uid = params.get("uid");
  const token = params.get("token");
  const confirming = useMemo(() => Boolean(uid && token), [uid, token]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      if (confirming) {
        if (!isStrongEnoughPassword(password)) {
          setError("Use uma senha com pelo menos 10 caracteres.");
          return;
        }
        await confirmPasswordReset({ uid, token, new_password: password });
        setMessage("Senha atualizada. Voce ja pode entrar.");
      } else {
        await requestPasswordReset(cleanText(email));
        setMessage("Se o email estiver cadastrado, voce recebera instrucoes.");
      }
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <AuthPanel title="Recuperar senha" subtitle="O fluxo usa resposta generica para proteger os dados dos clientes.">
      <form className="form" onSubmit={submit}>
        {confirming ? (
          <label>
            Nova senha
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
        ) : (
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
        )}
        {error && <p className="form-error">{error}</p>}
        {message && <p className="form-success">{message}</p>}
        <button className="primary-button full" type="submit">
          Enviar
          <MailCheck size={18} />
        </button>
      </form>
      <div className="auth-links">
        <Link to="/login">Voltar ao login</Link>
      </div>
    </AuthPanel>
  );
}
