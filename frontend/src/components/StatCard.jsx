export default function StatCard({ label, value, detail, icon: Icon }) {
  return (
    <article className="stat-card">
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        {detail && <small>{detail}</small>}
      </div>
      {Icon && (
        <span className="stat-icon">
          <Icon size={20} />
        </span>
      )}
    </article>
  );
}
