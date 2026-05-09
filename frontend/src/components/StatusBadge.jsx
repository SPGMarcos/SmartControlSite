const labels = {
  active: "Ativo",
  pending: "Pendente",
  past_due: "Em atraso",
  canceled: "Cancelado",
  paid: "Pago",
  failed: "Falhou",
  planning: "Planejamento",
  design: "Design",
  development: "Desenvolvimento",
  review: "Revisao",
  published: "Publicado",
  open: "Aberta",
  in_progress: "Em andamento",
  done: "Concluida",
  blocked: "Bloqueado"
};

export default function StatusBadge({ value }) {
  return <span className={`status status-${value || "neutral"}`}>{labels[value] || value || "Sem status"}</span>;
}
