import {
  ArrowRight,
  BadgeCheck,
  BriefcaseBusiness,
  Code2,
  CreditCard,
  Gauge,
  LockKeyhole,
  MessagesSquare,
  ShieldCheck,
  Store
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import PlanCatalog from "../components/PlanCatalog.jsx";
import PublicHeader from "../components/PublicHeader.jsx";
import { getPublicPlans } from "../services/dashboardService.js";
import { normalizePlans } from "../utils/plans.js";

const services = [
  { icon: Code2, title: "Landing pages", text: "Paginas rapidas, responsivas e orientadas para conversao." },
  { icon: Store, title: "Lojas online", text: "Experiencias de venda com checkout, catalogo e integracoes." },
  { icon: BriefcaseBusiness, title: "Sistemas web", text: "Portais e ferramentas sob medida para operacoes digitais." }
];

export default function LandingPage() {
  const [plans, setPlans] = useState([]);
  const [plansLoading, setPlansLoading] = useState(true);
  const [plansError, setPlansError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadPlans() {
      setPlansLoading(true);
      setPlansError("");
      try {
        const data = await getPublicPlans();
        if (active) setPlans(normalizePlans(data));
      } catch (error) {
        if (active) setPlansError(error.message);
      } finally {
        if (active) setPlansLoading(false);
      }
    }

    loadPlans();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="site-page">
      <PublicHeader />

      <section className="hero" data-reveal>
        <div className="hero-scene" aria-hidden="true">
          <div className="scene-topbar" />
          <div className="scene-panel scene-panel-main">
            <span />
            <strong />
            <small />
            <div className="scene-bars">
              <i />
              <i />
              <i />
            </div>
          </div>
          <div className="scene-panel scene-panel-side">
            <span />
            <span />
            <span />
          </div>
          <div className="scene-panel scene-panel-bottom">
            <i />
            <i />
            <i />
            <i />
          </div>
        </div>
        <div className="hero-content">
          <span className="eyebrow">
            <ShieldCheck size={16} />
            Sites profissionais com gestao e assinatura
          </span>
          <h1>SmartControl Sites</h1>
          <p>
            Venda, entregue e acompanhe landing pages, lojas online e sistemas web com uma plataforma segura para clientes e administracao.
          </p>
          <div className="hero-actions">
            <Link className="primary-button large" to="/register">
              Solicitar projeto
              <ArrowRight size={20} />
            </Link>
            <a className="secondary-button large" href="#planos">
              Ver planos
            </a>
          </div>
          <div className="trust-row">
            <span>
              <LockKeyhole size={17} />
              Auth segura
            </span>
            <span>
              <CreditCard size={17} />
              Stripe
            </span>
            <span>
              <Gauge size={17} />
              Painel em tempo real
            </span>
          </div>
        </div>
      </section>

      <section className="section" id="servicos" data-reveal>
        <div className="section-heading">
          <span>Servicos</span>
          <h2>Da primeira pagina ao sistema completo.</h2>
        </div>
        <div className="service-grid">
          {services.map((service) => (
            <article className="card interactive-card" key={service.title} data-reveal>
              <service.icon size={24} />
              <h3>{service.title}</h3>
              <p>{service.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="section" id="planos" data-reveal>
        <div className="section-heading">
          <span>Planos</span>
          <h2>Pagamento unico pelo projeto e assinatura para continuidade.</h2>
        </div>
        {plansError && <p className="notice error">{plansError}</p>}
        <PlanCatalog
          plans={plans}
          loading={plansLoading}
          renderAction={(plan) => (
            <Link className="secondary-button full" to={`/register?plan=${encodeURIComponent(plan.slug)}`}>
              Escolher
            </Link>
          )}
        />
      </section>

      <section className="section muted" id="processo" data-reveal>
        <div className="section-heading">
          <span>Como funciona</span>
          <h2>Um fluxo simples para vender, produzir e manter.</h2>
        </div>
        <div className="timeline">
          {["Briefing", "Proposta", "Desenvolvimento", "Publicacao", "Suporte mensal"].map((step, index) => (
            <article key={step} data-reveal>
              <span>{index + 1}</span>
              <h3>{step}</h3>
            </article>
          ))}
        </div>
      </section>

      <section className="final-cta" data-reveal>
        <BadgeCheck size={28} />
        <h2>Transforme sua presenca digital em uma operacao inteligente de vendas.</h2>
        <p>Sites, automacoes e gestao profissional para empresas que querem crescer com tecnologia, performance e confianca.</p>
        <Link className="primary-button large" to="/register">
          Criar conta
          <MessagesSquare size={20} />
        </Link>
      </section>
    </div>
  );
}
