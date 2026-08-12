import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import PageTransition from "./components/PageTransition.jsx";
import { useAuth } from "./hooks/useAuth.js";
import { useScrollReveal } from "./hooks/useScrollReveal.js";
import { AdminRoute, ProtectedRoute } from "./routes/ProtectedRoute.jsx";

const AdminPage = lazy(() => import("./pages/AdminPage.jsx"));
const BillingPage = lazy(() => import("./pages/BillingPage.jsx"));
const DashboardPage = lazy(() => import("./pages/DashboardPage.jsx"));
const LandingPage = lazy(() => import("./pages/LandingPage.jsx"));
const LoginPage = lazy(() => import("./pages/LoginPage.jsx"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage.jsx"));
const RegisterPage = lazy(() => import("./pages/RegisterPage.jsx"));
const ResetPasswordPage = lazy(() => import("./pages/ResetPasswordPage.jsx"));

function PageLoader() {
  return (
    <div className="screen-center">
      <p className="notice">Carregando pagina...</p>
    </div>
  );
}

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
      <Suspense fallback={<PageLoader />}>
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
      </Suspense>
    </PageTransition>
  );
}
