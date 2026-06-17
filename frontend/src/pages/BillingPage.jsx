import { CreditCard, ExternalLink, ReceiptText, Repeat, WalletCards } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import AppShell from "../components/AppShell.jsx";
import PlanCatalog from "../components/PlanCatalog.jsx";
import StatCard from "../components/StatCard.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { createCheckoutSession, createCustomerPortalSession, getPayments, getPlans, getProjects, getSubscriptions } from "../services/dashboardService.js";
import { asArray, money, normalizePlans } from "../utils/plans.js";

function date(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR").format(new Date(value));
}

const payableStatuses = new Set(["quote_sent", "payment_pending", "awaiting_analysis"]);

function canPayProject(project) {
  return Boolean(project.plan_id && payableStatuses.has(project.status));
}

export default function BillingPage() {
  const [searchParams] = useSearchParams();
  const [projects, setProjects] = useState([]);
  const [plans, setPlans] = useState([]);
  const [payments, setPayments] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    const results = await Promise.allSettled([getProjects(), getPlans(), getPayments(), getSubscriptions()]);
    if (results[0].status === "fulfilled") setProjects(asArray(results[0].value));
    if (results[1].status === "fulfilled") setPlans(normalizePlans(results[1].value));
    if (results[2].status === "fulfilled") setPayments(asArray(results[2].value));
    if (results[3].status === "fulfilled") setSubscriptions(asArray(results[3].value));
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
  const pendingPayments = useMemo(() => payments.filter((item) => item.status === "pending"), [payments]);
  const paidTotal = useMemo(
    () => payments.filter((item) => item.status === "paid").reduce((sum, item) => sum + Number(item.amount || 0), 0),
    [payments]
  );
  const payableProjects = useMemo(
    () => projects.filter((project) => canPayProject(project)),
    [projects]
  );

  const checkout = async (payload, label) => {
    setError("");
    setAction(label);
    try {
      const session = await createCheckoutSession(payload);
      window.location.assign(session.checkoutUrl);
    } catch (item) {
      setAction("");
      setError(item.message);
    }
  };

  const openPortal = async () => {
    setError("");
    setAction("Abrindo assinatura");
    try {
      const session = await createCustomerPortalSession();
      window.location.assign(session.portalUrl);
    } catch (item) {
      setAction("");
      setError(item.message);
    }
  };

  return (
    <AppShell>
      <header className="app-header">
        <div>
          <span className="eyebrow">Billing / checkout</span>
          <h1>Pagamentos</h1>
          <p>Projetos, assinaturas e historico financeiro em uma unica tela.</p>
        </div>
      </header>

      {searchParams.get("checkout") === "success" && <p className="notice success">Pagamento recebido pela Stripe. A confirmacao final acontece pelo webhook.</p>}
      {searchParams.get("checkout") === "cancel" && <p className="notice">Checkout cancelado.</p>}
      {error && <p className="notice error">{error}</p>}
      {loading && <p className="notice">Carregando billing...</p>}

      <section className="stats-grid">
        <StatCard label="Assinatura" value={activeSubscription?.plan_name || "Sem assinatura"} detail={<StatusBadge value={activeSubscription?.status} />} icon={Repeat} />
        <StatCard label="Pagamentos pendentes" value={pendingPayments.length} detail="Aguardando confirmacao" icon={ReceiptText} />
        <StatCard label="Projetos a pagar" value={payableProjects.length} detail="Com orcamento vinculado" icon={WalletCards} />
        <StatCard label="Total pago" value={money(paidTotal)} detail="Confirmado" icon={CreditCard} />
      </section>

      <section className="dashboard-grid">
        <section className="billing-products span-3">
          <div className="panel-heading">
            <div>
              <h2>Planos e produtos</h2>
              <p className="section-note">Os mesmos produtos da Home, sincronizados pela API.</p>
            </div>
          </div>
          <PlanCatalog
            plans={plans}
            loading={loading && plans.length === 0}
            renderAction={(plan) => (
              <div className="plan-actions">
                <button className="secondary-button full" type="button" disabled={Boolean(action) || plan.setupPrice <= 0} onClick={() => checkout({ plan_id: plan.id, kind: "one_time" }, "Abrindo checkout do projeto")}>
                  <CreditCard size={17} />
                  {plan.setupPrice > 0 ? "Pagar projeto" : "Solicitar proposta"}
                </button>
                <button className="primary-button full" type="button" disabled={Boolean(action) || plan.monthlyPrice <= 0} onClick={() => checkout({ plan_id: plan.id, kind: "subscription" }, "Abrindo assinatura")}>
                  <Repeat size={17} />
                  {plan.monthlyPrice > 0 ? "Assinar suporte" : "Sob medida"}
                </button>
              </div>
            )}
          />
          {action && <p className="notice">Processando: {action}...</p>}
        </section>

        <article className="panel span-2">
          <div className="panel-heading">
            <h2>Projetos para pagamento</h2>
          </div>
          <div className="table-like">
            {projects.map((project) => (
              <div className="table-row align-start" key={project.id}>
                <div>
                  <strong>{project.name}</strong>
                  <span>{project.plan_name || "Aguardando orcamento"}</span>
                  <StatusBadge value={project.status} />
                </div>
                <div className="row-actions">
                  <button className="secondary-button" type="button" disabled={!canPayProject(project) || Boolean(action)} onClick={() => checkout({ project_id: project.id, kind: "one_time" }, "Abrindo checkout")}>
                    <CreditCard size={17} />
                    Pagar
                  </button>
                  <button className="secondary-button" type="button" disabled={!canPayProject(project) || Boolean(action)} onClick={() => checkout({ project_id: project.id, kind: "installment", installments: 12 }, "Abrindo parcelamento")}>
                    <WalletCards size={17} />
                    Parcelar
                  </button>
                </div>
              </div>
            ))}
            {projects.length === 0 && <p className="empty">Nenhum projeto encontrado.</p>}
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h2>Assinatura</h2>
          </div>
          <div className="stack-list">
            <div className="compact-item">
              <div>
                <strong>{activeSubscription?.plan_name || "Sem plano ativo"}</strong>
                <span>{activeSubscription?.current_period_end ? `Renova em ${date(activeSubscription.current_period_end)}` : "Portal Stripe"}</span>
              </div>
              <StatusBadge value={activeSubscription?.status} />
            </div>
            <button className="primary-button full" type="button" onClick={openPortal} disabled={Boolean(action)}>
              <ExternalLink size={18} />
              Gerenciar assinatura
            </button>
          </div>
        </article>

        <article className="panel">
          <div className="panel-heading">
            <h2>Historico</h2>
          </div>
          <div className="table-like">
            {payments.slice(0, 8).map((payment) => (
              <div className="table-row" key={payment.id}>
                <div>
                  <strong>{money(payment.amount, payment.currency)}</strong>
                  <span>{payment.project_name || payment.kind}</span>
                </div>
                <StatusBadge value={payment.status} />
              </div>
            ))}
            {payments.length === 0 && <p className="empty">Nenhum pagamento registrado.</p>}
          </div>
        </article>
      </section>
    </AppShell>
  );
}
