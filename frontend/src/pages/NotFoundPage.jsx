import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <main className="screen-center">
      <h1>Pagina nao encontrada</h1>
      <Link className="primary-button" to="/">
        Voltar
      </Link>
    </main>
  );
}
