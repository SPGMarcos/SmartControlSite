from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
import stripe

from apps.clients.models import Client
from apps.core.permissions import IsAdmin, IsAdminOrReadOnly
from apps.projects.models import Project

from .models import Payment, Plan, Subscription, TransactionLog
from .serializers import CheckoutSessionSerializer, PaymentSerializer, PlanSerializer, SubscriptionSerializer, TransactionLogSerializer
from .services import StripeBillingService, StripeWebhookService


logger = logging.getLogger(__name__)


def get_or_create_billing_client(user):
    client = Client.objects.select_related("user").filter(user=user).first()
    if client:
        return client
    if user.role != "client":
        raise ValidationError("Apenas clientes podem iniciar checkout.")

    company_name = " ".join(item for item in [user.first_name, user.last_name] if item).strip() or user.email
    client, _ = Client.objects.select_related("user").get_or_create(
        user=user,
        defaults={"company_name": company_name},
    )
    return client


def stripe_error_response(exc):
    logger.exception("Stripe API request failed: %s", exc)
    return Response(
        {"detail": "Stripe nao conseguiu processar a solicitacao. Verifique chaves, modo test/live, produtos/precos e configuracao da conta."},
        status=status.HTTP_502_BAD_GATEWAY,
    )


class PlanViewSet(ModelViewSet):
    serializer_class = PlanSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ("is_active",)
    search_fields = ("name", "slug", "description")
    ordering_fields = ("setup_price", "monthly_price", "name")

    def get_queryset(self):
        queryset = Plan.objects.all()
        user = self.request.user
        if not user.is_authenticated or user.role != "admin":
            return queryset.filter(is_active=True)
        return queryset


class SubscriptionViewSet(ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ("status", "client", "plan", "project")
    search_fields = ("client__company_name", "client__user__email", "plan__name", "project__name")
    ordering_fields = ("created_at", "current_period_end", "status")

    def get_queryset(self):
        queryset = Subscription.objects.select_related("client", "client__user", "plan", "project")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(client__user=self.request.user)

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdmin()]
        return super().get_permissions()


class PaymentViewSet(ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ("status", "kind", "client")
    search_fields = ("client__company_name", "client__user__email", "stripe_checkout_session_id", "stripe_payment_intent_id", "stripe_invoice_id")
    ordering_fields = ("created_at", "paid_at", "amount", "status")

    def get_queryset(self):
        queryset = Payment.objects.select_related("client", "client__user", "subscription", "project")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(client__user=self.request.user)


class TransactionLogViewSet(ReadOnlyModelViewSet):
    serializer_class = TransactionLogSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ("provider", "event_type", "status", "client", "project", "payment")
    search_fields = ("stripe_event_id", "event_type", "client__company_name", "client__user__email", "project__name")
    ordering_fields = ("created_at", "event_type", "status", "amount")

    def get_queryset(self):
        return TransactionLog.objects.select_related("client", "client__user", "subscription", "project", "payment")


class CheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "checkout"

    def post(self, request):
        serializer = CheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client = get_or_create_billing_client(request.user)
        project = None
        if serializer.validated_data.get("project_id"):
            project = get_object_or_404(Project.objects.select_related("plan"), pk=serializer.validated_data["project_id"], client=client)

        if project and project.plan_id:
            plan = project.plan
        elif project:
            raise ValidationError("Projeto ainda nao possui orcamento/plano para pagamento.")
        else:
            plan = get_object_or_404(Plan, pk=serializer.validated_data.get("plan_id"), is_active=True)

        try:
            session = StripeBillingService.create_checkout_session(
                client=client,
                plan=plan,
                kind=serializer.validated_data["kind"],
                project=project,
                request=request,
                installments=serializer.validated_data.get("installments"),
                include_setup=serializer.validated_data.get("include_setup", False),
            )
        except stripe.error.StripeError as exc:
            return stripe_error_response(exc)
        return Response({"checkoutUrl": session["url"], "sessionId": session["id"]})

    def get(self, request):
        session_id = request.query_params.get("session_id", "").strip()
        if not session_id:
            raise ValidationError("Informe a sessao de checkout.")

        client = get_or_create_billing_client(request.user)
        try:
            result = StripeBillingService.sync_checkout_session(client=client, session_id=session_id, request=request)
        except stripe.error.StripeError as exc:
            return stripe_error_response(exc)

        return Response(
            {
                "sessionId": result["session_id"],
                "status": result["status"],
                "paymentStatus": result["payment_status"],
                "mode": result["mode"],
                "amountTotal": result["amount_total"],
                "currency": result["currency"],
                "subscription": SubscriptionSerializer(result["subscription"]).data if result["subscription"] else None,
                "payment": PaymentSerializer(result["payment"]).data if result["payment"] else None,
            }
        )


class CustomerPortalSessionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "checkout"

    def post(self, request):
        client = get_or_create_billing_client(request.user)
        try:
            session = StripeBillingService.create_portal_session(client=client, request=request)
        except stripe.error.StripeError as exc:
            return stripe_error_response(exc)
        return Response({"portalUrl": session["url"], "sessionId": session["id"]})


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        if not settings.STRIPE_WEBHOOK_SECRET:
            return Response({"detail": "Webhook secret nao configurado."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = stripe.Webhook.construct_event(request.body, signature, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response({"detail": "Invalid webhook."}, status=status.HTTP_400_BAD_REQUEST)

        result = StripeWebhookService.handle(event)
        return Response(result)
