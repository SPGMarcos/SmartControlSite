import {
  ArrowRight,
  BadgeCheck,
  BriefcaseBusiness,
  Check,
  Code2,
  CreditCard,
  Gauge,
  LifeBuoy,
  LockKeyhole,
  MessagesSquare,
  RefreshCw,
  ServerCog,
  ShieldCheck,
  Store
} from "lucide-react";
import { Link } from "react-router-dom";

import PublicHeader from "../components/PublicHeader.jsx";

const services = [
  { icon: Code2, title: "Landing pages", text: "Paginas rapidas, responsivas e orientadas para conversao." },
  { icon: Store, title: "Lojas online", text: "Experiencias de venda com checkout, catalogo e integracoes." },
  { icon: BriefcaseBusiness, title: "Sistemas web", text: "Portais e ferramentas sob medida para operacoes digitais." }
];

const portfolio = [
  { title: "Horizon Digital", type: "Landing", status: "Publicado" },
  { title: "Ecommerce local", type: "Loja", status: "Crescimento" },
  { title: "Portal de servicos", type: "Sistema", status: "Operacao" }
];

const plans = [
  {
    name: "Start",
    price: "R$ 799",
    monthly: "R$ 99/mes",
    monthlyTitle: "Assinatura opcional de suporte",
    monthlyText: "Hospedagem, manutencao, seguranca e pequenos ajustes mensais.",
    icon: LifeBuoy,
    items: ["Landing page", "Hospedagem assistida", "Painel do cliente"]
  },
  {
    name: "Business",
    price: "R$ 1.990",
    monthly: "R$ 249/mes",
    monthlyTitle: "Operacao recorrente",
    monthlyText: "Suporte, atualizacoes, melhorias de performance e acompanhamento.",
    icon: ServerCog,
    items: ["Site completo", "SEO tecnico", "Suporte mensal"]
  },
  {
    name: "Scale",
    price: "Sob medida",
    monthly: "Contrato recorrente",
    monthlyTitle: "SLA e evolucao continua",
    monthlyText: "Roadmap, automacoes, integracoes e suporte prioritario.",
    icon: RefreshCw,
    items: ["Sistema web", "Integracoes", "SLA prioritario"]
  }
];

export default function LandingPage() {
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

      <section className="section muted" id="portfolio" data-reveal>
        <div className="section-heading">
          <span>Portfolio</span>
          <h2>Projetos com visual limpo, performance e manutencao.</h2>
        </div>
        <div className="portfolio-grid">
          {portfolio.map((item, index) => (
            <article className="portfolio-item interactive-card" key={item.title} data-reveal>
              <div className={`portfolio-preview preview-${index + 1}`}>
                <span />
                <strong />
                <i />
                <i />
              </div>
              <div>
                <h3>{item.title}</h3>
                <p>{item.type}</p>
              </div>
              <span className="mini-status">{item.status}</span>
            </article>
          ))}
        </div>
      </section>

      <section className="section" id="planos" data-reveal>
        <div className="section-heading">
          <span>Planos</span>
          <h2>Pagamento unico pelo projeto e assinatura para continuidade.</h2>
        </div>
        <div className="plans-grid">
          {plans.map((plan) => (
            <article className="plan-card interactive-card" key={plan.name} data-reveal>
              <h3>{plan.name}</h3>
              <div className="plan-price">
                <span>Projeto unico</span>
                <strong>{plan.price}</strong>
              </div>
              <div className="monthly-note">
                <span className="monthly-icon">
                  <plan.icon size={18} />
                </span>
                <div>
                  <span>{plan.monthlyTitle}</span>
                  <strong>{plan.monthly}</strong>
                  <small>{plan.monthlyText}</small>
                </div>
              </div>
              <ul>
                {plan.items.map((item) => (
                  <li key={item}>
                    <Check size={17} />
                    {item}
                  </li>
                ))}
              </ul>
              <Link className="secondary-button full" to="/register">
                Escolher
              </Link>
            </article>
          ))}
        </div>
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
