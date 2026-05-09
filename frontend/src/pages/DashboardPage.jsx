import { CreditCard, FolderKanban, MessageSquarePlus, RefreshCcw, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import AppShell from "../components/AppShell.jsx";
import StatCard from "../components/StatCard.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { createRequest, getClientProfile, getPayments, getProjects, getRequests, getSubscriptions } from "../services/dashboardService.js";
import { cleanText } from "../utils/security.js";

function asArray(value) {
  return Array.isArray(value) ? value : value?.results || [];
}

function money(value, currency = "BRL") {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(value || 0));
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [client, setClient] = useState(null);
  const [projects, setProjects] = useState([]);
  const [requests, setRequests] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [payments, setPayments] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [requestForm, setRequestForm] = useState({ project_id: "", title: "", description: "", priority: "medium" });

  const load = async () => {
    setLoading(true);
    setError("");
    const results = await Promise.allSettled([
      getClientProfile(),
      getProjects(),
      getRequests(),
      getSubscriptions(),
      getPayments()
    ]);

    if (results[0].status === "fulfilled") setClient(results[0].value);
    if (results[1].status === "fulfilled") {
      const items = asArray(results[1].value);
      setProjects(items);
      setRequestForm((current) => ({ ...current, project_id: current.project_id || items[0]?.id || "" }));
    }
    if (results[2].status === "fulfilled") setRequests(asArray(results[2].value));
    if (results[3].status === "fulfilled") setSubscriptions(asArray(results[3].value));
    if (results[4].status === "fulfilled") setPayments(asArray(results[4].value));

    const rejected = results.find((item) => item.status === "rejected");
    if (rejected) setError(rejected.reason.message);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  const activeSubscription = useMemo(
    () => subscriptions.find((item) => item.status === "active") || subscriptions[0],
    [subscriptions]
  );
  const paidTotal = useMemo(
    () => payments.filter((item) => item.status === "paid").reduce((sum, item) => sum + Number(item.amount || 0), 0),
    [payments]
  );

  const submitRequest = async (event) => {
    event.preventDefault();
    if (!requestForm.project_id) return;
    await createRequest({
      project_id: Number(requestForm.project_id),
      title: cleanText(requestForm.title),
      description: cleanText(requestForm.description),
      priority: requestForm.priority
    });
    setRequestForm((current) => ({ ...current, title: "", description: "" }));
    await load();
  };

  return (
    <AppShell>
      <header className="app-header">
        <div>
          <span className="eyebrow">Area do cliente</span>
          <h1>Ola, {user?.first_name || client?.company_name || "cliente"}</h1>
          <p>Acompanhe seu plano, status do projeto, historico financeiro e solicitacoes.</p>
        </div>
        <button className="secondary-button" type="button" onClick={load}>
          <RefreshCcw size={18} />
          Atualizar
        </button>
      </header>

      {error && <p className="notice error">{error}</p>}
      {loading && <p className="notice">Carregando dados...</p>}

      <section className="stats-grid">
        <StatCard label="Plano atual" value={activeSubscription?.plan_name || "Sem assinatura"} detail={<StatusBadge value={activeSubscription?.status} />} icon={ShieldCheck} />
        <StatCard label="Projetos" value={projects.length} detail="Sites em acompanhamento" icon={FolderKanban} />
        <StatCard label="Solicitacoes" value={requests.length} detail="Historico do cliente" icon={MessageSquarePlus} />
        <StatCard label="Pagamentos" value={money(paidTotal)} detail="Total confirmado" icon={CreditCard} />
      </section>

      <section className="dashboard-grid">
        <article className="panel span-2">
          <div className="panel-heading">
            <h2>Projetos</h2>
          </div>
          <div className="table-like">
            {projects.length === 0 && <p className="empty">Nenhum projeto cadastrado ainda.</p>}
            {projects.map((project) => (
              <div className="table-row" key={project.id}>
                <div>
                  <strong>{project.name}</strong>
                  <span>{project.domain || project.site_type}</span>
                </div>
                <StatusBadge value={project.status} />
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h2>Dados do site</h2>
          </div>
          <dl className="info-list">
            <div>
              <dt>Empresa</dt>
              <dd>{client?.company_name || "-"}</dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>
                <StatusBadge value={client?.status} />
              </dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{user?.email}</dd>
            </div>
          </dl>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h2>Nova solicitacao</h2>
          </div>
          <form className="form compact" onSubmit={submitRequest}>
            <label>
              Projeto
              <select value={requestForm.project_id} onChange={(event) => setRequestForm({ ...requestForm, project_id: event.target.value })}>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Titulo
              <input value={requestForm.title} onChange={(event) => setRequestForm({ ...requestForm, title: event.target.value })} required />
            </label>
            <label>
              Descricao
              <textarea value={requestForm.description} onChange={(event) => setRequestForm({ ...requestForm, description: event.target.value })} required />
            </label>
            <button className="primary-button full" type="submit" disabled={!projects.length}>
              Enviar
            </button>
          </form>
        </article>

        <article className="panel span-2">
          <div className="panel-heading">
            <h2>Historico</h2>
          </div>
          <div className="table-like">
            {requests.slice(0, 6).map((item) => (
              <div className="table-row" key={item.id}>
                <div>
                  <strong>{item.title}</strong>
                  <span>{item.project_name}</span>
                </div>
                <StatusBadge value={item.status} />
              </div>
            ))}
            {requests.length === 0 && <p className="empty">Sem solicitacoes registradas.</p>}
          </div>
        </article>
      </section>
    </AppShell>
  );
}
