export function asArray(value) {
  return Array.isArray(value) ? value : value?.results || [];
}

export function money(value, currency = "BRL") {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency }).format(Number(value || 0));
}

export function normalizePlan(plan) {
  const setupPrice = Number(plan.setup_price || 0);
  const monthlyPrice = Number(plan.monthly_price || 0);

  return {
    ...plan,
    setupPrice,
    monthlyPrice,
    setupLabel: setupPrice > 0 ? money(setupPrice) : "Sob medida",
    monthlyLabel: monthlyPrice > 0 ? `${money(monthlyPrice)} / mes` : "Contrato recorrente",
    monthlyTitle: plan.monthly_title || "Continuidade e suporte",
    monthlyText: plan.description || "Suporte, manutencao e evolucao continua conforme o plano contratado.",
    features: Array.isArray(plan.features) ? plan.features.filter(Boolean) : [],
  };
}

export function normalizePlans(value) {
  return asArray(value).map(normalizePlan);
}
