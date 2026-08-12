import {
  ArrowUpDown,
  Banknote,
  BriefcaseBusiness,
  ClipboardList,
  CreditCard,
  Eye,
  ExternalLink,
  Filter,
  Gauge,
  LayoutDashboard,
  LifeBuoy,
  Link as LinkIcon,
  Plus,
  RefreshCcw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Store,
  UsersRound
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import AppShell from "../components/AppShell.jsx";
import StatCard from "../components/StatCard.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { useAuth } from "../hooks/useAuth.js";
import {
  createPlan,
  getAdminDashboard,
  updateProject
} from "../services/adminService.js";
import { API_BASE_URL } from "../services/api.js";
import { cleanText } from "../utils/security.js";

function asArray(value) {
  return Array.isArray(value) ? value : value?.results || [];
}

function money(value, currency = "BRL") {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(value || 0));
}

function date(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR").format(new Date(value));
}

function dateTime(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function normalizeText(value) {
  return String(value || "").toLowerCase();
}

function matchesSearch(item, fields, query) {
  const needle = normalizeText(query);
  if (!needle) return true;
  return fields.some((field) => normalizeText(field(item)).includes(needle));
}

function sortItems(items, sortKey, direction, resolvers) {
  const resolver = resolvers[sortKey] || ((item) => item?.[sortKey]);
  return [...items].sort((a, b) => {
    const left = resolver(a);
    const right = resolver(b);
    if (left === right) return 0;
    if (left === undefined || left === null) return 1;
    if (right === undefined || right === null) return -1;
    if (typeof left === "number" && typeof right === "number") {
      return direction === "asc" ? left - right : right - left;
    }
    return direction === "asc"
      ? String(left).localeCompare(String(right))
      : String(right).localeCompare(String(left));
  });
}

const tabs = [
  ["overview", "Dashboard", LayoutDashboard],
  ["sales", "Vendas", CreditCard],
  ["clients", "Clientes", UsersRound],
  ["sites", "Sites", Store],
  ["access", "Acessos", LinkIcon],
  ["support", "Suporte", LifeBuoy],
];

const projectStatuses = [
  ["awaiting_analysis", "Aguardando analise"],
  ["quote_sent", "Orcamento enviado"],
  ["payment_pending", "Pagamento pendente"],
  ["in_development", "Em desenvolvimento"],
  ["review", "Revisao"],
  ["completed", "Concluido"]
];

const requestStatuses = [
  ["open", "Aberta"],
  ["in_progress", "Em andamento"],
  ["waiting_client", "Aguardando cliente"],
  ["done", "Concluida"],
  ["canceled", "Cancelada"],
];

const saleSorters = {
  created_at: (item) => item.created_at || "",
  amount: (item) => Number(item.amount || 0),
  client: (item) => item.client_company || "",
  status: (item) => item.status || "",
};

const clientSorters = {
  created_at: (item) => item.created_at || "",
  company_name: (item) => item.company_name || "",
  status: (item) => item.status || "",
  purchases: (item) => item.purchaseCount || 0,
};

const projectSorters = {
  created_at: (item) => item.created_at || "",
  updated_at: (item) => item.updated_at || "",
  name: (item) => item.name || "",
  status: (item) => item.status || "",
};

const emptyMetrics = Object.freeze({
  paidSales: 0,
  paymentsTotal: 0,
  revenue: "0",
  clientsTotal: 0,
  newClients: 0,
  activeSites: 0,
  soldSites: 0,
  projectsInDevelopment: 0,
  activeSubscriptions: 0,
  subscriptionsTotal: 0,
  conversionRate: 0,
  openSupportRequests: 0,
});

function AdminToolbar({ query, setQuery, activeTab, setActiveTab, loading, load }) {
  return (
    <section className="admin-toolbar" aria-label="Navegacao administrativa">
      <div className="admin-tabs">
        {tabs.map(([value, label, Icon]) => (
          <button className={activeTab === value ? "is-active" : ""} key={value} type="button" onClick={() => setActiveTab(value)}>
            <Icon size={17} />
            {label}
          </button>
        ))}
      </div>
      <div className="admin-search">
        <Search size={18} />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar em vendas, clientes, sites e suporte" />
      </div>
      <button className="secondary-button" type="button" onClick={() => load({ forceSync: true })} disabled={loading}>
        <RefreshCcw size={17} />
        {loading ? "Atualizando" : "Atualizar"}
      </button>
    </section>
  );
}

function AdminPanel({ title, icon: Icon, children, action, className = "" }) {
  return (
    <article className={`panel admin-panel ${className}`}>
      <div className="panel-heading">
        <h2>
          {Icon && <Icon size={19} />}
          {title}
        </h2>
        {action}
      </div>
      {children}
    </article>
  );
}

function EmptyState({ children }) {
  return <p className="empty admin-empty">{children}</p>;
}

function FilterBar({ children }) {
  return (
    <div className="admin-filterbar">
      <Filter size={17} />
      {children}
    </div>
  );
}

function DetailPanel({ selected, onClose }) {
  if (!selected) return null;

  return (
    <aside className="admin-detail-panel" aria-live="polite">
      <div className="panel-heading">
        <h2>{selected.title}</h2>
        <button className="ghost-button" type="button" onClick={onClose}>
          Fechar
        </button>
      </div>
      <dl className="info-list">
        {selected.rows.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value || "-"}</dd>
          </div>
        ))}
      </dl>
    </aside>
  );
}

function PlanForm({ action, submitPlan, planForm, setPlanForm }) {
  return (
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
        Titulo recorrente
        <input value={planForm.monthly_title} onChange={(event) => setPlanForm({ ...planForm, monthly_title: event.target.value })} placeholder="Assinatura opcional de suporte" />
      </label>
      <label>
        Descricao recorrente
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
      <button className="primary-button full" type="submit" disabled={Boolean(action)}>
        <Plus size={18} />
        {action === "Criando plano" ? "Criando..." : "Criar plano"}
      </button>
    </form>
  );
}

export default function AdminPage() {
  const navigate = useNavigate();
  const { enterUserPreviewMode } = useAuth();
  const [activeTab, setActiveTab] = useState("overview");
  const [query, setQuery] = useState("");
  const [clients, setClients] = useState([]);
  const [projects, setProjects] = useState([]);
  const [plans, setPlans] = useState([]);
  const [payments, setPayments] = useState([]);
  const [requests, setRequests] = useState([]);
  const [transactionLogs, setTransactionLogs] = useState([]);
  const [adminStatus, setAdminStatus] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [hasLoadedSnapshot, setHasLoadedSnapshot] = useState(false);
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState("");
  const [saleFilter, setSaleFilter] = useState("all");
  const [saleSort, setSaleSort] = useState("created_at");
  const [saleDirection, setSaleDirection] = useState("desc");
  const [clientFilter, setClientFilter] = useState("all");
  const [clientSort, setClientSort] = useState("created_at");
  const [projectFilter, setProjectFilter] = useState("all");
  const [projectSort, setProjectSort] = useState("updated_at");
  const [requestFilter, setRequestFilter] = useState("all");
  const [planForm, setPlanForm] = useState({
    name: "",
    slug: "",
    setup_price: "",
    monthly_price: "",
    monthly_title: "",
    description: "",
    features: "",
    stripe_setup_price_id: "",
    stripe_monthly_price_id: ""
  });

  const load = async ({ forceSync = false } = {}) => {
    setLoading(true);
    setError("");
    try {
      const snapshot = await getAdminDashboard({ forceSync });
      setAdminStatus(snapshot.adminStatus);
      setMetrics({ ...emptyMetrics, ...(snapshot.metrics || {}) });
      setClients(asArray(snapshot.clients));
      setProjects(asArray(snapshot.projects));
      setPlans(asArray(snapshot.plans));
      setPayments(asArray(snapshot.payments));
      setRequests(asArray(snapshot.requests));
      setTransactionLogs(asArray(snapshot.transactionLogs));
      setHasLoadedSnapshot(true);
    } catch (item) {
      setError(item.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const newClients = useMemo(() => {
    const now = Date.now();
    const windowMs = 30 * 24 * 60 * 60 * 1000;
    return clients.filter((client) => client.created_at && now - new Date(client.created_at).getTime() <= windowMs);
  }, [clients]);

  const paymentsByClient = useMemo(() => {
    const map = new Map();
    payments.forEach((payment) => {
      const current = map.get(payment.client) || [];
      current.push(payment);
      map.set(payment.client, current);
    });
    return map;
  }, [payments]);

  const projectsByClient = useMemo(() => {
    const map = new Map();
    projects.forEach((project) => {
      const current = map.get(project.client_id) || [];
      current.push(project);
      map.set(project.client_id, current);
    });
    return map;
  }, [projects]);

  const enrichedClients = useMemo(
    () => clients.map((client) => {
      const clientPayments = paymentsByClient.get(client.id) || [];
      const clientProjects = projectsByClient.get(client.id) || [];
      return {
        ...client,
        purchaseCount: clientPayments.length,
        paidTotal: clientPayments.filter((payment) => payment.status === "paid").reduce((sum, payment) => sum + Number(payment.amount || 0), 0),
        projectCount: clientProjects.length,
      };
    }),
    [clients, paymentsByClient, projectsByClient]
  );

  const recentActivity = useMemo(() => {
    const items = [
      ...payments.map((item) => ({ type: "Pagamento", title: `${money(item.amount, item.currency)} - ${item.client_company || "Cliente"}`, status: item.status, created_at: item.created_at })),
      ...projects.map((item) => ({ type: "Site", title: item.name, status: item.status, created_at: item.updated_at || item.created_at })),
      ...requests.map((item) => ({ type: "Suporte", title: item.title, status: item.status, created_at: item.updated_at || item.created_at })),
      ...transactionLogs.slice(0, 12).map((item) => ({ type: "Stripe", title: item.event_type, status: item.status, created_at: item.created_at })),
    ];
    return items.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)).slice(0, 10);
  }, [payments, projects, requests, transactionLogs]);

  const filteredSales = useMemo(() => {
    const filtered = payments.filter((item) => {
      const matchesStatus = saleFilter === "all" || item.status === saleFilter || item.kind === saleFilter;
      return matchesStatus && matchesSearch(item, [
        (sale) => sale.client_company,
        (sale) => sale.project_name,
        (sale) => sale.status,
        (sale) => sale.kind,
        (sale) => sale.stripe_checkout_session_id,
        (sale) => sale.stripe_invoice_id,
      ], query);
    });
    return sortItems(filtered, saleSort, saleDirection, saleSorters);
  }, [payments, query, saleDirection, saleFilter, saleSort]);

  const filteredClients = useMemo(() => {
    const filtered = enrichedClients.filter((client) => {
      const matchesStatus = clientFilter === "all" || client.status === clientFilter;
      return matchesStatus && matchesSearch(client, [
        (item) => item.company_name,
        (item) => item.user?.email,
        (item) => item.phone,
        (item) => item.status,
      ], query);
    });
    return sortItems(filtered, clientSort, "desc", clientSorters);
  }, [clientFilter, clientSort, enrichedClients, query]);

  const filteredProjects = useMemo(() => {
    const filtered = projects.filter((project) => {
      const matchesStatus = projectFilter === "all" || project.status === projectFilter || project.site_type === projectFilter;
      return matchesStatus && matchesSearch(project, [
        (item) => item.name,
        (item) => item.client_company,
        (item) => item.plan_name,
        (item) => item.domain,
        (item) => item.production_url,
        (item) => item.status,
      ], query);
    });
    return sortItems(filtered, projectSort, "desc", projectSorters);
  }, [projectFilter, projectSort, projects, query]);

  const filteredRequests = useMemo(() => {
    return requests.filter((item) => {
      const matchesStatus = requestFilter === "all" || item.status === requestFilter || item.priority === requestFilter;
      return matchesStatus && matchesSearch(item, [
        (request) => request.title,
        (request) => request.description,
        (request) => request.client_company,
        (request) => request.project_name,
        (request) => request.status,
        (request) => request.priority,
      ], query);
    });
  }, [query, requestFilter, requests]);

  const submitPlan = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setAction("Criando plano");
    const features = planForm.features
      .split("\n")
      .map((item) => cleanText(item))
      .filter(Boolean);
    try {
      await createPlan({
        name: cleanText(planForm.name),
        slug: cleanText(planForm.slug),
        description: cleanText(planForm.description),
        setup_price: planForm.setup_price || 0,
        monthly_price: planForm.monthly_price || 0,
        monthly_title: cleanText(planForm.monthly_title),
        features,
        is_active: true,
        stripe_setup_price_id: cleanText(planForm.stripe_setup_price_id),
        stripe_monthly_price_id: cleanText(planForm.stripe_monthly_price_id)
      });
      setPlanForm({ name: "", slug: "", setup_price: "", monthly_price: "", monthly_title: "", description: "", features: "", stripe_setup_price_id: "", stripe_monthly_price_id: "" });
      setSuccess("Plano criado com sucesso.");
      await load();
    } catch (item) {
      setError(item.message);
    } finally {
      setAction("");
    }
  };

  const openUserPreview = async () => {
    setError("");
    setSuccess("");
    setAction("Validando permissao administrativa");
    try {
      await enterUserPreviewMode();
      navigate("/dashboard");
    } catch (item) {
      setError(item.message);
    } finally {
      setAction("");
    }
  };

  const changeProjectStatus = async (project, status) => {
    const sensitive = status === "completed" || project.status === "completed";
    if (sensitive && !window.confirm(`Confirmar alteracao de status do site "${project.name}"?`)) return;

    setError("");
    setSuccess("");
    setAction(`Atualizando ${project.name}`);
    try {
      await updateProject(project.id, { status });
      setSuccess("Status do site atualizado.");
      await load();
    } catch (item) {
      setError(item.message);
    } finally {
      setAction("");
    }
  };

  const changeProjectPlan = async (project, planId) => {
    if (!planId && project.plan_id && !window.confirm(`Remover plano vinculado ao site "${project.name}"?`)) return;

    setError("");
    setSuccess("");
    setAction(`Vinculando plano a ${project.name}`);
    try {
      await updateProject(project.id, {
        plan_id: planId ? Number(planId) : null,
        status: planId && project.status === "awaiting_analysis" ? "quote_sent" : project.status
      });
      setSuccess("Plano do site atualizado.");
      await load();
    } catch (item) {
      setError(item.message);
    } finally {
      setAction("");
    }
  };

  const selectSale = (sale) => {
    const log = transactionLogs.find((item) => item.payment === sale.id || item.stripe_event_id === sale.stripe_invoice_id);
    setSelected({
      title: `Venda #${sale.id}`,
      rows: [
        ["Cliente", sale.client_company],
        ["Produto/site", sale.project_name || sale.kind],
        ["Valor", money(sale.amount, sale.currency)],
        ["Pagamento", <StatusBadge value={sale.status} />],
        ["Tipo", sale.kind],
        ["Data", dateTime(sale.paid_at || sale.created_at)],
        ["Stripe checkout", sale.stripe_checkout_session_id],
        ["Stripe invoice", sale.stripe_invoice_id],
        ["Historico", log ? `${log.event_type} (${log.status})` : "Sem log relacionado carregado"],
      ],
    });
  };

  const selectClient = (client) => {
    const clientProjects = projectsByClient.get(client.id) || [];
    const clientPayments = paymentsByClient.get(client.id) || [];
    setSelected({
      title: client.company_name,
      rows: [
        ["Email", client.user?.email],
        ["Telefone", client.phone],
        ["Documento", client.document],
        ["Status", <StatusBadge value={client.status} />],
        ["Cadastro", dateTime(client.created_at)],
        ["Sites associados", clientProjects.length],
        ["Compras", clientPayments.length],
        ["Receita paga", money(client.paidTotal)],
      ],
    });
  };

  const selectProject = (project) => {
    const projectPayments = payments.filter((payment) => payment.project === project.id);
    setSelected({
      title: project.name,
      rows: [
        ["Cliente", project.client_company],
        ["Plano/produto", project.plan_name],
        ["Status", <StatusBadge value={project.status} />],
        ["Tipo", project.site_type],
        ["Dominio", project.domain],
        ["URL de producao", project.production_url ? <a href={project.production_url} target="_blank" rel="noreferrer">{project.production_url}</a> : "-"],
        ["Criado em", dateTime(project.created_at)],
        ["Atualizado em", dateTime(project.updated_at)],
        ["Compras vinculadas", projectPayments.length],
      ],
    });
  };

  const renderOverview = () => (
    <>
      <section className="stats-grid admin-stats">
        <StatCard label="Vendas" value={metrics.paidSales} detail={`${metrics.paymentsTotal} pagamentos registrados`} icon={CreditCard} />
        <StatCard label="Receita" value={money(metrics.revenue)} detail="Pagamentos confirmados" icon={Banknote} />
        <StatCard label="Clientes" value={metrics.clientsTotal} detail={`${metrics.newClients} novos em 30 dias`} icon={UsersRound} />
        <StatCard label="Novos clientes" value={metrics.newClients} detail="Ultimos 30 dias" icon={UsersRound} />
        <StatCard label="Sites ativos" value={metrics.activeSites} detail={`${metrics.soldSites} vendidos/em execucao`} icon={Store} />
        <StatCard label="Sites vendidos" value={metrics.soldSites} detail="Com pagamento ou em producao" icon={Store} />
        <StatCard label="Em desenvolvimento" value={metrics.projectsInDevelopment} detail="Pipeline atual" icon={BriefcaseBusiness} />
        <StatCard label="Assinaturas ativas" value={metrics.activeSubscriptions} detail={`${metrics.subscriptionsTotal} assinaturas no total`} icon={ShieldCheck} />
        <StatCard label="Conversao" value={`${metrics.conversionRate}%`} detail="Clientes com pagamento pago" icon={Gauge} />
        <StatCard label="Suporte aberto" value={metrics.openSupportRequests} detail="Solicitacoes pendentes" icon={LifeBuoy} />
      </section>

      <section className="admin-overview-grid">
        <AdminPanel className="span-2" title="Atividades recentes" icon={ClipboardList}>
          <div className="admin-timeline">
            {recentActivity.map((item, index) => (
              <button className="admin-activity" key={`${item.type}-${item.title}-${index}`} type="button">
                <span>{item.type}</span>
                <strong>{item.title}</strong>
                <small>{dateTime(item.created_at)}</small>
                <StatusBadge value={item.status} />
              </button>
            ))}
            {recentActivity.length === 0 && <EmptyState>Nenhuma atividade registrada ainda.</EmptyState>}
          </div>
        </AdminPanel>

        <AdminPanel title="Central rapida" icon={LinkIcon}>
          <div className="admin-shortcuts compact">
            <button type="button" onClick={() => setActiveTab("sales")}>Vendas</button>
            <button type="button" onClick={() => setActiveTab("clients")}>Clientes</button>
            <button type="button" onClick={() => setActiveTab("sites")}>Sites</button>
            <button type="button" onClick={() => setActiveTab("support")}>Suporte</button>
            <Link to="/dashboard">Area do usuario</Link>
            <Link to="/billing">Billing</Link>
          </div>
        </AdminPanel>
      </section>
    </>
  );

  const renderSales = () => (
    <section className="admin-workspace-grid">
      <AdminPanel className="span-2" title="Vendas" icon={CreditCard}>
        <FilterBar>
          <select value={saleFilter} onChange={(event) => setSaleFilter(event.target.value)}>
            <option value="all">Todos os status/tipos</option>
            <option value="paid">Pagas</option>
            <option value="pending">Pendentes</option>
            <option value="failed">Falhas</option>
            <option value="one_time">Projeto unico</option>
            <option value="subscription">Assinatura</option>
            <option value="installment">Parcelamento</option>
          </select>
          <select value={saleSort} onChange={(event) => setSaleSort(event.target.value)}>
            <option value="created_at">Data</option>
            <option value="amount">Valor</option>
            <option value="client">Cliente</option>
            <option value="status">Status</option>
          </select>
          <button className="ghost-button" type="button" onClick={() => setSaleDirection((current) => current === "desc" ? "asc" : "desc")}>
            <ArrowUpDown size={16} />
            {saleDirection === "desc" ? "Desc" : "Asc"}
          </button>
        </FilterBar>
        <div className="admin-table">
          <div className="admin-table-head sales">
            <span>Cliente</span>
            <span>Produto/site</span>
            <span>Valor</span>
            <span>Data</span>
            <span>Status</span>
          </div>
          {filteredSales.map((sale) => (
            <button className="admin-table-row sales" key={sale.id} type="button" onClick={() => selectSale(sale)}>
              <span>{sale.client_company || "-"}</span>
              <span>{sale.project_name || sale.kind}</span>
              <strong>{money(sale.amount, sale.currency)}</strong>
              <span>{date(sale.paid_at || sale.created_at)}</span>
              <StatusBadge value={sale.status} />
            </button>
          ))}
          {filteredSales.length === 0 && <EmptyState>Nenhuma venda encontrada com os filtros atuais.</EmptyState>}
        </div>
      </AdminPanel>

      <AdminPanel title="Historico Stripe" icon={SlidersHorizontal}>
        <div className="stack-list">
          {transactionLogs.slice(0, 10).map((log) => (
            <div className="compact-item align-start" key={log.id}>
              <div>
                <strong>{log.event_type}</strong>
                <span>{log.client_company || log.project_name || "Evento sem cliente vinculado"}</span>
                <small>{dateTime(log.created_at)}</small>
              </div>
              <StatusBadge value={log.status} />
            </div>
          ))}
          {transactionLogs.length === 0 && <EmptyState>Nenhum log transacional carregado.</EmptyState>}
        </div>
      </AdminPanel>
    </section>
  );

  const renderClients = () => (
    <section className="admin-workspace-grid">
      <AdminPanel className="span-2" title="Clientes" icon={UsersRound}>
        <FilterBar>
          <select value={clientFilter} onChange={(event) => setClientFilter(event.target.value)}>
            <option value="all">Todos os status</option>
            <option value="active">Ativos</option>
            <option value="inactive">Inativos</option>
            <option value="blocked">Bloqueados</option>
          </select>
          <select value={clientSort} onChange={(event) => setClientSort(event.target.value)}>
            <option value="created_at">Cadastro</option>
            <option value="company_name">Empresa</option>
            <option value="status">Status</option>
            <option value="purchases">Compras</option>
          </select>
        </FilterBar>
        <div className="admin-table">
          <div className="admin-table-head clients">
            <span>Cliente</span>
            <span>Status</span>
            <span>Sites</span>
            <span>Compras</span>
            <span>Cadastro</span>
          </div>
          {filteredClients.map((client) => (
            <button className="admin-table-row clients" key={client.id} type="button" onClick={() => selectClient(client)}>
              <span>
                <strong>{client.company_name}</strong>
                <small>{client.user?.email}</small>
              </span>
              <StatusBadge value={client.status} />
              <span>{client.projectCount}</span>
              <span>{client.purchaseCount} / {money(client.paidTotal)}</span>
              <span>{date(client.created_at)}</span>
            </button>
          ))}
          {filteredClients.length === 0 && <EmptyState>Nenhum cliente encontrado.</EmptyState>}
        </div>
      </AdminPanel>

      <AdminPanel title="Novos clientes" icon={UsersRound}>
        <div className="stack-list">
          {newClients.slice(0, 8).map((client) => (
            <button className="compact-item align-start admin-list-button" key={client.id} type="button" onClick={() => selectClient(enrichedClients.find((item) => item.id === client.id) || client)}>
              <div>
                <strong>{client.company_name}</strong>
                <span>{client.user?.email}</span>
                <small>{dateTime(client.created_at)}</small>
              </div>
              <StatusBadge value={client.status} />
            </button>
          ))}
          {newClients.length === 0 && <EmptyState>Nenhum cliente novo nos ultimos 30 dias.</EmptyState>}
        </div>
      </AdminPanel>
    </section>
  );

  const renderSites = () => (
    <section className="admin-workspace-grid">
      <AdminPanel className="span-2" title="Sites e projetos" icon={Store}>
        <FilterBar>
          <select value={projectFilter} onChange={(event) => setProjectFilter(event.target.value)}>
            <option value="all">Todos os sites</option>
            {projectStatuses.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            <option value="landing_page">Landing page</option>
            <option value="institutional_site">Site institucional</option>
            <option value="web_system">Sistema web</option>
          </select>
          <select value={projectSort} onChange={(event) => setProjectSort(event.target.value)}>
            <option value="updated_at">Ultima atualizacao</option>
            <option value="created_at">Criacao</option>
            <option value="name">Nome</option>
            <option value="status">Status</option>
          </select>
        </FilterBar>
        <div className="admin-table">
          <div className="admin-table-head sites">
            <span>Site</span>
            <span>Cliente</span>
            <span>Plano</span>
            <span>Status</span>
            <span>Acoes</span>
          </div>
          {filteredProjects.map((project) => (
            <div className="admin-table-row sites" key={project.id}>
              <button type="button" onClick={() => selectProject(project)}>
                <strong>{project.name}</strong>
                <small>{project.production_url || project.domain || project.site_type}</small>
              </button>
              <span>{project.client_company}</span>
              <select className="mini-select" value={project.plan_id || ""} onChange={(event) => changeProjectPlan(project, event.target.value)} disabled={Boolean(action)}>
                <option value="">Sem plano</option>
                {plans.map((plan) => (
                  <option key={plan.id} value={plan.id}>
                    {plan.name}
                  </option>
                ))}
              </select>
              <select className="mini-select" value={project.status} onChange={(event) => changeProjectStatus(project, event.target.value)} disabled={Boolean(action)}>
                {projectStatuses.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
              <span className="row-actions">
                {project.production_url && (
                  <a className="ghost-button" href={project.production_url} target="_blank" rel="noreferrer">
                    <ExternalLink size={16} />
                  </a>
                )}
                <StatusBadge value={project.status} />
              </span>
            </div>
          ))}
          {filteredProjects.length === 0 && <EmptyState>Nenhum site encontrado.</EmptyState>}
        </div>
      </AdminPanel>

      <AdminPanel title="Planos" icon={BriefcaseBusiness}>
        <div className="stack-list">
          {plans.map((plan) => (
            <div className="compact-item align-start" key={plan.id}>
              <div>
                <strong>{plan.name}</strong>
                <span>{money(plan.setup_price)} + {money(plan.monthly_price)}/mes</span>
                <small>{plan.slug}</small>
              </div>
              <StatusBadge value={plan.is_active ? "active" : "inactive"} />
            </div>
          ))}
          {plans.length === 0 && <EmptyState>Nenhum plano cadastrado.</EmptyState>}
        </div>
      </AdminPanel>

      <AdminPanel title="Novo plano" icon={Plus}>
        <PlanForm action={action} planForm={planForm} setPlanForm={setPlanForm} submitPlan={submitPlan} />
      </AdminPanel>
    </section>
  );

  const renderAccess = () => {
    const apiOrigin = API_BASE_URL.replace(/\/api$/, "");
    const shortcuts = [
      ["Sistema", "Dashboard administrativo", "/admin", false],
      ["Area do usuario", "Dashboard do cliente", "/dashboard", false],
      ["Billing", "Pagamentos do usuario", "/billing", false],
      ["Publico", "Landing page", "/", false],
      ["API", "Health check", `${API_BASE_URL}/health/`, true],
      ["API", "Django admin", `${apiOrigin}/admin/`, true],
      ["Docs", "Arquitetura", "https://github.com/spgmarcos/SmartControlSite/blob/main/docs/ARCHITECTURE.md", true],
      ["Docs", "Deploy", "https://github.com/spgmarcos/SmartControlSite/blob/main/docs/DEPLOY.md", true],
    ];

    return (
      <section className="admin-workspace-grid">
        <AdminPanel className="span-2" title="Central de acessos" icon={LinkIcon}>
          <div className="admin-shortcuts">
            {shortcuts.map(([group, label, href, external]) => external ? (
              <a href={href} key={`${group}-${label}`} target="_blank" rel="noreferrer">
                <span>{group}</span>
                <strong>{label}</strong>
                <ExternalLink size={17} />
              </a>
            ) : (
              <Link to={href} key={`${group}-${label}`}>
                <span>{group}</span>
                <strong>{label}</strong>
                <ExternalLink size={17} />
              </Link>
            ))}
          </div>
        </AdminPanel>

        <AdminPanel title="Sessao segura" icon={ShieldCheck}>
          <dl className="info-list">
            <div>
              <dt>Admin validado</dt>
              <dd>{adminStatus?.admin ? "Sim" : "Nao"}</dd>
            </div>
            <div>
              <dt>Email</dt>
              <dd>{adminStatus?.user?.email || "-"}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{adminStatus?.user?.role || "-"}</dd>
            </div>
            <div>
              <dt>API</dt>
              <dd>{API_BASE_URL}</dd>
            </div>
          </dl>
        </AdminPanel>
      </section>
    );
  };

  const renderSupport = () => (
    <section className="admin-workspace-grid">
      <AdminPanel className="span-2" title="Suporte" icon={LifeBuoy}>
        <FilterBar>
          <select value={requestFilter} onChange={(event) => setRequestFilter(event.target.value)}>
            <option value="all">Todas as solicitacoes</option>
            {requestStatuses.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            <option value="urgent">Urgente</option>
            <option value="high">Alta prioridade</option>
          </select>
        </FilterBar>
        <div className="admin-table">
          <div className="admin-table-head support">
            <span>Solicitacao</span>
            <span>Cliente</span>
            <span>Projeto</span>
            <span>Prioridade</span>
            <span>Status</span>
          </div>
          {filteredRequests.map((request) => (
            <button className="admin-table-row support" key={request.id} type="button" onClick={() => setSelected({
              title: request.title,
              rows: [
                ["Cliente", request.client_company],
                ["Projeto", request.project_name],
                ["Status", <StatusBadge value={request.status} />],
                ["Prioridade", request.priority],
                ["Criado por", request.created_by_email],
                ["Criado em", dateTime(request.created_at)],
                ["Atualizado em", dateTime(request.updated_at)],
                ["Descricao", request.description],
              ],
            })}>
              <span>
                <strong>{request.title}</strong>
                <small>{request.description}</small>
              </span>
              <span>{request.client_company}</span>
              <span>{request.project_name}</span>
              <span>{request.priority}</span>
              <StatusBadge value={request.status} />
            </button>
          ))}
          {filteredRequests.length === 0 && <EmptyState>Nenhuma solicitacao encontrada.</EmptyState>}
        </div>
      </AdminPanel>

      <AdminPanel title="Clientes que precisam de atencao" icon={LifeBuoy}>
        <div className="stack-list">
          {requests.filter((item) => ["open", "in_progress", "waiting_client"].includes(item.status)).slice(0, 10).map((request) => (
            <div className="compact-item align-start" key={request.id}>
              <div>
                <strong>{request.client_company || "Cliente"}</strong>
                <span>{request.title}</span>
                <small>{dateTime(request.created_at)}</small>
              </div>
              <StatusBadge value={request.status} />
            </div>
          ))}
          {requests.filter((item) => ["open", "in_progress", "waiting_client"].includes(item.status)).length === 0 && <EmptyState>Nenhum atendimento pendente.</EmptyState>}
        </div>
      </AdminPanel>
    </section>
  );

  return (
    <AppShell>
      <header className="app-header admin-header">
        <div>
          <span className="eyebrow">Painel administrativo</span>
          <h1>Central de controle</h1>
          <p>Vendas, clientes, sites, acessos e suporte usando somente dados reais do sistema.</p>
        </div>
        <div className="admin-header-actions">
          {adminStatus?.admin && (
            <button className="primary-button" type="button" onClick={openUserPreview} disabled={Boolean(action)}>
              <Eye size={18} />
              Visualizar como usuário
            </button>
          )}
          {adminStatus?.admin && (
            <div className="admin-session-badge">
              <ShieldCheck size={18} />
              <span>{adminStatus.user?.email}</span>
            </div>
          )}
        </div>
      </header>

      <AdminToolbar activeTab={activeTab} loading={loading} load={load} query={query} setActiveTab={setActiveTab} setQuery={setQuery} />

      {error && <p className="notice error">{error}</p>}
      {success && <p className="notice success">{success}</p>}
      {loading && <p className="notice">{hasLoadedSnapshot ? "Atualizando dados administrativos..." : "Carregando dados administrativos..."}</p>}
      {action && <p className="notice">Processando: {action}...</p>}

      {hasLoadedSnapshot && metrics && (
        <div className={`admin-content-shell ${selected ? "has-detail" : ""}`}>
          <main>
            {activeTab === "overview" && renderOverview()}
            {activeTab === "sales" && renderSales()}
            {activeTab === "clients" && renderClients()}
            {activeTab === "sites" && renderSites()}
            {activeTab === "access" && renderAccess()}
            {activeTab === "support" && renderSupport()}
          </main>
          <DetailPanel selected={selected} onClose={() => setSelected(null)} />
        </div>
      )}
    </AppShell>
  );
}
