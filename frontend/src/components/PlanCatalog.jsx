import { Check, LifeBuoy, RefreshCw, ServerCog } from "lucide-react";

const iconBySlug = {
  start: LifeBuoy,
  business: ServerCog,
  scale: RefreshCw,
};

function planIcon(plan) {
  return iconBySlug[String(plan.slug || "").toLowerCase()] || RefreshCw;
}

export default function PlanCatalog({ plans, renderAction, loading = false, emptyMessage = "Nenhum plano disponivel." }) {
  if (loading) {
    return <p className="notice">Carregando planos...</p>;
  }

  if (!plans.length) {
    return <p className="empty">{emptyMessage}</p>;
  }

  return (
    <div className="plans-grid">
      {plans.map((plan) => {
        const Icon = planIcon(plan);

        return (
          <article className="plan-card interactive-card" key={plan.id || plan.slug}>
            <h3>{plan.name}</h3>
            <div className="plan-price">
              <span>Projeto unico</span>
              <strong>{plan.setupLabel}</strong>
            </div>
            <div className="monthly-note">
              <span className="monthly-icon">
                <Icon size={18} />
              </span>
              <div>
                <span>{plan.monthlyTitle}</span>
                <strong>{plan.monthlyLabel}</strong>
                <small>{plan.monthlyText}</small>
              </div>
            </div>
            {plan.features.length > 0 && (
              <ul>
                {plan.features.map((item) => (
                  <li key={item}>
                    <Check size={17} />
                    {item}
                  </li>
                ))}
              </ul>
            )}
            {renderAction?.(plan)}
          </article>
        );
      })}
    </div>
  );
}
