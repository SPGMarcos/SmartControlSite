from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.billing.views import CheckoutSessionView, PaymentViewSet, PlanViewSet, StripeWebhookView, SubscriptionViewSet
from apps.clients.views import ClientViewSet
from apps.core.views import csrf, health
from apps.projects.views import ProjectViewSet, ServiceRequestViewSet
from apps.users.views import CookieTokenRefreshView, LoginView, LogoutView, MeView, PasswordResetConfirmView, PasswordResetRequestView, RegisterView

router = DefaultRouter()
router.register("clients", ClientViewSet, basename="clients")
router.register("plans", PlanViewSet, basename="plans")
router.register("subscriptions", SubscriptionViewSet, basename="subscriptions")
router.register("payments", PaymentViewSet, basename="payments")
router.register("projects", ProjectViewSet, basename="projects")
router.register("requests", ServiceRequestViewSet, basename="requests")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/csrf/", csrf, name="csrf"),
    path("api/auth/register/", RegisterView.as_view(), name="register"),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/me/", MeView.as_view(), name="me"),
    path("api/auth/token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/password-reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("api/auth/password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("api/billing/checkout-session/", CheckoutSessionView.as_view(), name="checkout_session"),
    path("api/billing/webhook/stripe/", StripeWebhookView.as_view(), name="stripe_webhook"),
    path("api/", include(router.urls)),
]
