from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
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

        client = Client.objects.select_related("user").get(user=request.user)
        project = None
        if serializer.validated_data.get("project_id"):
            project = get_object_or_404(Project.objects.select_related("plan"), pk=serializer.validated_data["project_id"], client=client)

        if project and project.plan_id:
            plan = project.plan
        elif project:
            raise ValidationError("Projeto ainda nao possui orcamento/plano para pagamento.")
        else:
            plan = get_object_or_404(Plan, pk=serializer.validated_data.get("plan_id"), is_active=True)

        session = StripeBillingService.create_checkout_session(
            client=client,
            plan=plan,
            kind=serializer.validated_data["kind"],
            project=project,
            request=request,
            installments=serializer.validated_data.get("installments"),
        )
        return Response({"checkoutUrl": session["url"], "sessionId": session["id"]})


class CustomerPortalSessionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "checkout"

    def post(self, request):
        client = Client.objects.select_related("user").get(user=request.user)
        session = StripeBillingService.create_portal_session(client=client, request=request)
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
