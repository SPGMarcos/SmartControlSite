from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
import stripe

from apps.clients.models import Client
from apps.core.permissions import IsAdmin, IsAdminOrReadOnly
from apps.projects.models import Project

from .models import Payment, Plan, Subscription
from .serializers import CheckoutSessionSerializer, PaymentSerializer, PlanSerializer, SubscriptionSerializer
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
    filterset_fields = ("status", "client", "plan")
    search_fields = ("client__company_name", "client__user__email", "plan__name")
    ordering_fields = ("created_at", "current_period_end", "status")

    def get_queryset(self):
        queryset = Subscription.objects.select_related("client", "client__user", "plan")
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
    search_fields = ("client__company_name", "client__user__email", "stripe_payment_intent_id", "stripe_invoice_id")
    ordering_fields = ("created_at", "paid_at", "amount", "status")

    def get_queryset(self):
        queryset = Payment.objects.select_related("client", "client__user", "subscription", "project")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(client__user=self.request.user)


class CheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "checkout"

    def post(self, request):
        serializer = CheckoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        client = Client.objects.select_related("user").get(user=request.user)
        plan = Plan.objects.get(pk=serializer.validated_data["plan_id"], is_active=True)
        project = None
        if serializer.validated_data.get("project_id"):
            project = Project.objects.get(pk=serializer.validated_data["project_id"], client=client)

        session = StripeBillingService.create_checkout_session(
            client=client,
            plan=plan,
            kind=serializer.validated_data["kind"],
            project=project,
            request=request,
        )
        return Response({"checkoutUrl": session["url"], "sessionId": session["id"]})


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = stripe.Webhook.construct_event(request.body, signature, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response({"detail": "Invalid webhook."}, status=status.HTTP_400_BAD_REQUEST)

        result = StripeWebhookService.handle(event)
        return Response(result)
