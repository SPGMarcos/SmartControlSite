import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import PageTransition from "./components/PageTransition.jsx";
import { useAuth } from "./hooks/useAuth.js";
import { useScrollReveal } from "./hooks/useScrollReveal.js";
import AdminPage from "./pages/AdminPage.jsx";
import BillingPage from "./pages/BillingPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import LandingPage from "./pages/LandingPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import ResetPasswordPage from "./pages/ResetPasswordPage.jsx";
import { AdminRoute, ProtectedRoute } from "./routes/ProtectedRoute.jsx";

function HomeRoute() {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="screen-center">
        <p className="notice">Carregando sessao...</p>
      </div>
    );
  }

  if (isAuthenticated) {
    return (
      <ProtectedRoute>
        <DashboardPage />
      </ProtectedRoute>
    );
  }

  return <LandingPage />;
}

export default function App() {
  const location = useLocation();
  useScrollReveal(location.pathname);

  return (
    <PageTransition key={location.pathname}>
      <Routes location={location}>
        <Route path="/" element={<HomeRoute />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/billing"
          element={
            <ProtectedRoute>
              <BillingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <AdminPage />
            </AdminRoute>
          }
        />
        <Route path="/app" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </PageTransition>
  );
}
