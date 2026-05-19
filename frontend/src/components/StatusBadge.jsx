const labels = {
  active: "Ativo",
  pending: "Pendente",
  past_due: "Em atraso",
  canceled: "Cancelado",
  paid: "Pago",
  failed: "Falhou",
  refunded: "Reembolsado",
  unpaid: "Nao pago",
  incomplete: "Incompleto",
  planning: "Planejamento",
  design: "Design",
  development: "Desenvolvimento",
  review: "Revisao",
  published: "Publicado",
  awaiting_analysis: "Aguardando analise",
  quote_sent: "Orcamento enviado",
  payment_pending: "Pagamento pendente",
  in_development: "Em desenvolvimento",
  completed: "Concluido",
  open: "Aberta",
  in_progress: "Em andamento",
  done: "Concluida",
  blocked: "Bloqueado"
};

export default function StatusBadge({ value }) {
  return <span className={`status status-${value || "neutral"}`}>{labels[value] || value || "Sem status"}</span>;
}
