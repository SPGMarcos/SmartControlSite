import { Navigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth.js";

export function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <main className="screen-center">Carregando...</main>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export function AdminRoute({ children }) {
  const { isAdmin, isAuthenticated, loading } = useAuth();

  if (loading) {
    return <main className="screen-center">Carregando...</main>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
