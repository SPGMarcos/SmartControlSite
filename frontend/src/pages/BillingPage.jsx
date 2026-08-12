import { CalendarClock, CreditCard, ExternalLink, ReceiptText, Repeat, WalletCards } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";

import AppShell from "../components/AppShell.jsx";
import PlanCatalog from "../components/PlanCatalog.jsx";
import StatCard from "../components/StatCard.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { createCheckoutSession, createCustomerPortalSession, getPayments, getPlans, getProjects, getSubscriptions, syncCheckoutSession } from "../services/dashboardService.js";
import { asArray, money, normalizePlans } from "../utils/plans.js";

function date(value) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("pt-BR").format(new Date(value));
}

const payableStatuses = new Set(["quote_sent", "payment_pending", "awaiting_analysis"]);
const paymentKindLabels = {
  one_time: "Projeto unico",
  subscription: "Assinatura",
  installment: "Parcelamento",
};

function canPayProject(project) {
  return Boolean(project.plan_id && payableStatuses.has(project.status));
}

export default function BillingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [projects, setProjects] = useState([]);
  const [plans, setPlans] = useState([]);
  const [payments, setPayments] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [checkoutResult, setCheckoutResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState("");
  const checkoutStartedRef = useRef(false);
  const checkoutSyncedRef = useRef(false);

  const load = async () => {
    setLoading(true);
    setError("");
    const results = await Promise.allSettled([getProjects(), getPlans(), getPayments(), getSubscriptions()]);
    if (results[0].status === "fulfilled") setProjects(asArray(results[0].value));
    if (results[1].status === "fulfilled") setPlans(normalizePlans(results[1].value));
    if (results[2].status === "fulfilled") setPayments(asArray(results[2].value));
    if (results[3].status === "fulfilled") setSubscriptions(asArray(results[3].value));
    if (results[1].status === "rejected") setError(results[1].reason.message);
    setLoading(false);
  };

  useEffect(() => {
    load();
  }, []);

  useEffect(() => {
    const checkoutStatus = searchParams.get("checkout");
    const sessionId = searchParams.get("session_id");
    if (checkoutStatus !== "success" || !sessionId || checkoutSyncedRef.current) return;

    checkoutSyncedRef.current = true;
    setAction("Atualizando dados da compra");
    syncCheckoutSession(sessionId)
      .then(async (result) => {
        setCheckoutResult(result);
        await load();
        setSearchParams((current) => {
          const next = new URLSearchParams(current);
          next.delete("session_id");
          return next;
        }, { replace: true });
      })
      .catch((item) => setError(item.message))
      .finally(() => setAction(""));
  }, [searchParams, setSearchParams]);

  const activeSubscription = useMemo(
    () => subscriptions.find((item) => item.status === "active") || subscriptions[0],
    [subscriptions]
  );
  const activePlan = useMemo(
    () => plans.find((plan) => Number(plan.id) === Number(activeSubscription?.plan)),
    [activeSubscription, plans]
  );
  const lastPayment = useMemo(
    () => payments.find((item) => item.status === "paid") || payments[0],
    [payments]
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

  const checkoutPlan = (plan) => {
    if (plan.setupPrice > 0 && plan.monthlyPrice > 0) {
      checkout({ plan_id: plan.id, kind: "subscription", include_setup: true }, "Abrindo projeto com manutencao");
      return;
    }

    if (plan.setupPrice > 0) {
      checkout({ plan_id: plan.id, kind: "one_time" }, "Abrindo checkout do projeto");
      return;
    }

    if (plan.monthlyPrice > 0) {
      checkout({ plan_id: plan.id, kind: "subscription" }, "Abrindo assinatura");
    }
  };

  useEffect(() => {
    if (loading || checkoutStartedRef.current || action) return;

    const planSlug = searchParams.get("plan");
    const pay = searchParams.get("pay");
    if (!planSlug || !pay) return;

    const plan = plans.find((item) => item.slug === planSlug);
    if (!plan) {
      if (plans.length > 0) setError("Plano selecionado nao foi encontrado.");
      return;
    }

    if (pay === "bundle" || (pay === "setup" && plan.monthlyPrice > 0)) {
      if (plan.setupPrice <= 0 || plan.monthlyPrice <= 0) {
        setError("Este plano ainda nao possui projeto e manutencao configurados para checkout conjunto.");
        return;
      }
      checkoutStartedRef.current = true;
      checkout({ plan_id: plan.id, kind: "subscription", include_setup: true }, "Abrindo projeto com manutencao");
      return;
    }

    if (pay === "setup") {
      if (plan.setupPrice <= 0) {
        setError("Este plano e sob medida. Solicite proposta para pagamento personalizado.");
        return;
      }
      checkoutStartedRef.current = true;
      checkout({ plan_id: plan.id, kind: "one_time" }, "Abrindo checkout do projeto");
    }

    if (pay === "subscription") {
      if (plan.monthlyPrice <= 0) {
        setError("Este plano nao possui assinatura mensal configurada.");
        return;
      }
      checkoutStartedRef.current = true;
      checkout(
        plan.setupPrice > 0 ? { plan_id: plan.id, kind: "subscription", include_setup: true } : { plan_id: plan.id, kind: "subscription" },
        plan.setupPrice > 0 ? "Abrindo projeto com manutencao" : "Abrindo assinatura"
      );
    }
  }, [action, loading, plans, searchParams]);

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

      {(activeSubscription || checkoutResult) && (
        <section className="billing-summary">
          <article className="billing-summary-main">
            <span className="eyebrow">Resumo atual</span>
            <h2>{activeSubscription?.plan_name || "Compra registrada"}</h2>
            <div className="summary-status-row">
              <StatusBadge value={activeSubscription?.status || (checkoutResult?.paymentStatus === "paid" ? "paid" : checkoutResult?.paymentStatus)} />
              <span>{activeSubscription?.current_period_end ? `Renova em ${date(activeSubscription.current_period_end)}` : "Aguardando atualizacao da Stripe"}</span>
            </div>
          </article>
          <article className="summary-metric">
            <CreditCard size={18} />
            <span>Cobrado hoje</span>
            <strong>{money(checkoutResult?.amountTotal ?? lastPayment?.amount ?? 0, checkoutResult?.currency || lastPayment?.currency || "BRL")}</strong>
          </article>
          <article className="summary-metric">
            <Repeat size={18} />
            <span>Assinatura mensal</span>
            <strong>{activePlan?.monthlyPrice > 0 ? activePlan.monthlyLabel : "Sem recorrencia"}</strong>
          </article>
          <article className="summary-metric">
            <CalendarClock size={18} />
            <span>Proxima renovacao</span>
            <strong>{activeSubscription?.current_period_end ? date(activeSubscription.current_period_end) : "-"}</strong>
          </article>
        </section>
      )}

      <section className="billing-plan-showcase">
        <div className="section-heading">
          <span>Planos</span>
          <h2>Pagamento unico pelo projeto e assinatura para continuidade.</h2>
        </div>
        <PlanCatalog
          plans={plans}
          loading={loading && plans.length === 0}
          renderAction={(plan) => (
            <div className="plan-actions">
              <button className="secondary-button full" type="button" disabled={Boolean(action) || (plan.setupPrice <= 0 && plan.monthlyPrice <= 0)} onClick={() => checkoutPlan(plan)}>
                <CreditCard size={17} />
                {plan.setupPrice > 0 || plan.monthlyPrice > 0 ? "Escolher" : "Solicitar proposta"}
              </button>
            </div>
          )}
        />
        {action && <p className="notice">Processando: {action}...</p>}
      </section>

      <section className="stats-grid">
        <StatCard label="Assinatura" value={activeSubscription?.plan_name || "Sem assinatura"} detail={<StatusBadge value={activeSubscription?.status} />} icon={Repeat} />
        <StatCard label="Pagamentos pendentes" value={pendingPayments.length} detail="Aguardando confirmacao" icon={ReceiptText} />
        <StatCard label="Projetos a pagar" value={payableProjects.length} detail="Com orcamento vinculado" icon={WalletCards} />
        <StatCard label="Total pago" value={money(paidTotal)} detail="Confirmado" icon={CreditCard} />
      </section>

      <section className="dashboard-grid">

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
                <span>{activePlan?.monthlyPrice > 0 ? `${activePlan.monthlyLabel} - ${activeSubscription?.current_period_end ? `renova em ${date(activeSubscription.current_period_end)}` : "recorrencia mensal"}` : "Portal Stripe"}</span>
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
                  <span>{payment.project_name || paymentKindLabels[payment.kind] || payment.kind}</span>
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
