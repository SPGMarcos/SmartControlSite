import { ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

export default function Logo({ to = "/", compact = false }) {
  return (
    <Link className="logo" to={to} aria-label="SmartControl Sites">
      <span className="logo-mark">
        <ShieldCheck size={20} />
      </span>
      {!compact && <span>SmartControl Sites</span>}
    </Link>
  );
}
