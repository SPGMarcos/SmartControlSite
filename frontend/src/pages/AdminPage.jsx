import { Banknote, BriefcaseBusiness, ClipboardList, Plus, UsersRound } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import AppShell from "../components/AppShell.jsx";
import StatCard from "../components/StatCard.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { createPlan, getAdminPayments, getAdminProjects, getAdminRequests, getClients, getPlans, updateProject } from "../services/adminService.js";
import { cleanText } from "../utils/security.js";

function asArray(value) {
  return Array.isArray(value) ? value : value?.results || [];
}

const projectStatuses = [
  ["awaiting_analysis", "Aguardando analise"],
  ["quote_sent", "Orcamento enviado"],
  ["payment_pending", "Pagamento pendente"],
  ["in_development", "Em desenvolvimento"],
  ["review", "Revisao"],
  ["completed", "Concluido"]
];

export default function AdminPage() {
  const [clients, setClients] = useState([]);
  const [projects, setProjects] = useState([]);
  const [plans, setPlans] = useState([]);
  const [payments, setPayments] = useState([]);
  const [requests, setRequests] = useState([]);
  const [error, setError] = useState("");
  const [planForm, setPlanForm] = useState({
    name: "",
    slug: "",
    setup_price: "",
    monthly_price: "",
    description: "",
    features: "",
    stripe_setup_price_id: "",
    stripe_monthly_price_id: ""
  });

  const load = async () => {
    setError("");
    const results = await Promise.allSettled([
      getClients(),
      getAdminProjects(),
      getPlans(),
      getAdminPayments(),
      getAdminRequests()
    ]);
    if (results[0].status === "fulfilled") setClients(asArray(results[0].value));
    if (results[1].status === "fulfilled") setProjects(asArray(results[1].value));
    if (results[2].status === "fulfilled") setPlans(asArray(results[2].value));
    if (results[3].status === "fulfilled") setPayments(asArray(results[3].value));
    if (results[4].status === "fulfilled") setRequests(asArray(results[4].value));
    const rejected = results.find((item) => item.status === "rejected");
    if (rejected) setError(rejected.reason.message);
  };

  useEffect(() => {
    load();
  }, []);

  const revenue = useMemo(
    () => payments.filter((item) => item.status === "paid").reduce((sum, item) => sum + Number(item.amount || 0), 0),
    [payments]
  );

  const submitPlan = async (event) => {
    event.preventDefault();
    const features = planForm.features
      .split("\n")
      .map((item) => cleanText(item))
      .filter(Boolean);
    await createPlan({
      name: cleanText(planForm.name),
      slug: cleanText(planForm.slug),
      description: cleanText(planForm.description),
      setup_price: planForm.setup_price || 0,
      monthly_price: planForm.monthly_price || 0,
      features,
      is_active: true,
      stripe_setup_price_id: cleanText(planForm.stripe_setup_price_id),
      stripe_monthly_price_id: cleanText(planForm.stripe_monthly_price_id)
    });
    setPlanForm({ name: "", slug: "", setup_price: "", monthly_price: "", description: "", features: "", stripe_setup_price_id: "", stripe_monthly_price_id: "" });
    await load();
  };

  const changeProjectStatus = async (project, status) => {
    setError("");
    try {
      await updateProject(project.id, { status });
      await load();
    } catch (item) {
      setError(item.message);
    }
  };

  const changeProjectPlan = async (project, planId) => {
    setError("");
    try {
      await updateProject(project.id, {
        plan_id: planId ? Number(planId) : null,
        status: planId && project.status === "awaiting_analysis" ? "quote_sent" : project.status
      });
      await load();
    } catch (item) {
      setError(item.message);
    }
  };

  return (
    <AppShell>
      <header className="app-header">
        <div>
          <span className="eyebrow">Painel administrativo</span>
          <h1>Controle operacional</h1>
          <p>Gerencie clientes, projetos, planos, pagamentos e solicitacoes em uma unica visao.</p>
        </div>
      </header>

      {error && <p className="notice error">{error}</p>}

      <section className="stats-grid">
        <StatCard label="Clientes" value={clients.length} detail="Contas cadastradas" icon={UsersRound} />
        <StatCard label="Projetos" value={projects.length} detail="Pipeline total" icon={BriefcaseBusiness} />
        <StatCard label="Solicitacoes" value={requests.length} detail="Fila operacional" icon={ClipboardList} />
        <StatCard label="Receita paga" value={new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(revenue)} detail="Confirmada" icon={Banknote} />
      </section>

      <section className="dashboard-grid">
        <article className="panel span-2">
          <div className="panel-heading">
            <h2>Clientes</h2>
          </div>
          <div className="table-like">
            {clients.map((client) => (
              <div className="table-row" key={client.id}>
                <div>
                  <strong>{client.company_name}</strong>
                  <span>{client.user?.email}</span>
                </div>
                <StatusBadge value={client.status} />
              </div>
            ))}
            {clients.length === 0 && <p className="empty">Nenhum cliente cadastrado.</p>}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h2>Novo plano</h2>
          </div>
          <form className="form compact" onSubmit={submitPlan}>
            <label>
              Nome
              <input value={planForm.name} onChange={(event) => setPlanForm({ ...planForm, name: event.target.value })} required />
            </label>
            <label>
              Slug
              <input value={planForm.slug} onChange={(event) => setPlanForm({ ...planForm, slug: event.target.value })} required />
            </label>
            <label>
              Setup
              <input type="number" min="0" step="0.01" value={planForm.setup_price} onChange={(event) => setPlanForm({ ...planForm, setup_price: event.target.value })} />
            </label>
            <label>
              Mensalidade
              <input type="number" min="0" step="0.01" value={planForm.monthly_price} onChange={(event) => setPlanForm({ ...planForm, monthly_price: event.target.value })} />
            </label>
            <label>
              Descricao
              <textarea value={planForm.description} onChange={(event) => setPlanForm({ ...planForm, description: event.target.value })} />
            </label>
            <label>
              Recursos
              <textarea value={planForm.features} onChange={(event) => setPlanForm({ ...planForm, features: event.target.value })} placeholder="Um recurso por linha" />
            </label>
            <label>
              Stripe setup price
              <input value={planForm.stripe_setup_price_id} onChange={(event) => setPlanForm({ ...planForm, stripe_setup_price_id: event.target.value })} placeholder="price_..." />
            </label>
            <label>
              Stripe mensal price
              <input value={planForm.stripe_monthly_price_id} onChange={(event) => setPlanForm({ ...planForm, stripe_monthly_price_id: event.target.value })} placeholder="price_..." />
            </label>
            <button className="primary-button full" type="submit">
              <Plus size={18} />
              Criar plano
            </button>
          </form>
        </article>

        <article className="panel span-2">
          <div className="panel-heading">
            <h2>Projetos</h2>
          </div>
          <div className="table-like">
            {projects.slice(0, 8).map((project) => (
              <div className="table-row align-start" key={project.id}>
                <div>
                  <strong>{project.name}</strong>
                  <span>{project.client_company} {project.plan_name ? `- ${project.plan_name}` : ""}</span>
                </div>
                <div className="row-actions">
                  <select className="mini-select" value={project.status} onChange={(event) => changeProjectStatus(project, event.target.value)}>
                    {projectStatuses.map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                  <select className="mini-select" value={project.plan_id || ""} onChange={(event) => changeProjectPlan(project, event.target.value)}>
                    <option value="">Sem plano</option>
                    {plans.map((plan) => (
                      <option key={plan.id} value={plan.id}>
                        {plan.name}
                      </option>
                    ))}
                  </select>
                  <StatusBadge value={project.status} />
                </div>
              </div>
            ))}
            {projects.length === 0 && <p className="empty">Nenhum projeto cadastrado.</p>}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h2>Planos</h2>
          </div>
          <div className="stack-list">
            {plans.map((plan) => (
              <div className="compact-item" key={plan.id}>
                <strong>{plan.name}</strong>
                <span>R$ {plan.setup_price} + R$ {plan.monthly_price}/mes</span>
              </div>
            ))}
          </div>
        </article>
      </section>
    </AppShell>
  );
}
