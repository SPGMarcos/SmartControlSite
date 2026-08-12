from datetime import timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
import stripe
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.billing.models import Payment, Plan, Subscription, TransactionLog
from apps.billing.serializers import PaymentSerializer, PlanSerializer, SubscriptionSerializer, TransactionLogSerializer
from apps.billing.services import effective_subscription_for_client
from apps.billing.views import BILLING_SYNC_CACHE_SECONDS, _wants_forced_sync, stripe_error_response, sync_billing_for_request_user
from apps.clients.models import Client
from apps.clients.serializers import ClientSerializer
from apps.projects.models import Project, ServiceRequest
from apps.projects.serializers import ProjectSerializer, ServiceRequestSerializer

from .permissions import IsAdmin


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([])
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


@api_view(["GET"])
@permission_classes([AllowAny])
@throttle_classes([])
def health(request):
    return Response(
        {
            "status": "ok",
            "checkout_bundle_enforced": True,
            "billing_sync_cache_seconds": BILLING_SYNC_CACHE_SECONDS,
        }
    )


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_status(request):
    return Response(
        {
            "status": "ok",
            "admin": True,
            "user": {
                "id": request.user.id,
                "email": request.user.email,
                "role": request.user.role,
            },
        }
    )


def _serialize(serializer_class, queryset, request):
    return serializer_class(queryset, many=True, context={"request": request}).data


def _effective_active_subscription_ids(*, clients):
    ids = set()
    for client in clients:
        subscription = effective_subscription_for_client(client)
        if subscription:
            ids.add(subscription.id)
    return ids


def _admin_metrics(*, clients, projects, payments, subscriptions, requests):
    clients_total = clients.count()
    paid_payments = payments.filter(status=Payment.Status.PAID)
    paid_client_count = paid_payments.values("client_id").distinct().count()
    revenue = paid_payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")
    new_clients_since = timezone.now() - timedelta(days=30)
    sold_project_statuses = [
        Project.Status.IN_DEVELOPMENT,
        Project.Status.REVIEW,
        Project.Status.COMPLETED,
    ]
    paid_project_ids = paid_payments.exclude(project_id__isnull=True).values("project_id")
    effective_active_subscription_ids = _effective_active_subscription_ids(clients=clients)

    return {
        "paidSales": paid_payments.count(),
        "paymentsTotal": payments.count(),
        "revenue": str(revenue),
        "clientsTotal": clients_total,
        "newClients": clients.filter(created_at__gte=new_clients_since).count(),
        "activeSites": projects.filter(
            Q(status=Project.Status.COMPLETED) | Q(production_url__gt="") | Q(domain__gt="")
        ).count(),
        "soldSites": projects.filter(
            Q(id__in=paid_project_ids) | Q(status__in=sold_project_statuses)
        ).distinct().count(),
        "projectsInDevelopment": projects.filter(status=Project.Status.IN_DEVELOPMENT).count(),
        "activeSubscriptions": len(effective_active_subscription_ids),
        "subscriptionsTotal": subscriptions.count(),
        "conversionRate": round((paid_client_count / clients_total) * 100) if clients_total else 0,
        "openSupportRequests": requests.filter(
            status__in=[
                ServiceRequest.Status.OPEN,
                ServiceRequest.Status.IN_PROGRESS,
                ServiceRequest.Status.WAITING_CLIENT,
            ]
        ).count(),
    }


@api_view(["GET"])
@permission_classes([IsAdmin])
def admin_dashboard(request):
    try:
        sync_result = sync_billing_for_request_user(request, force=_wants_forced_sync(request))
    except stripe.error.StripeError as exc:
        return stripe_error_response(exc)

    clients = Client.objects.select_related("user")
    projects = Project.objects.select_related("client", "plan", "client__user").prefetch_related("attachments")
    plans = Plan.objects.all()
    payments = Payment.objects.select_related("client", "client__user", "subscription", "project")
    subscriptions = Subscription.objects.select_related("client", "client__user", "plan", "project")
    requests = ServiceRequest.objects.select_related("project", "client", "created_by", "client__user")
    transaction_logs = TransactionLog.objects.select_related("client", "client__user", "subscription", "project", "payment")

    return Response(
        {
            "status": "ok",
            "syncedAt": timezone.now().isoformat(),
            "sync": sync_result,
            "adminStatus": {
                "status": "ok",
                "admin": True,
                "user": {
                    "id": request.user.id,
                    "email": request.user.email,
                    "role": request.user.role,
                },
            },
            "metrics": _admin_metrics(
                clients=clients,
                projects=projects,
                payments=payments,
                subscriptions=subscriptions,
                requests=requests,
            ),
            "clients": _serialize(ClientSerializer, clients, request),
            "projects": _serialize(ProjectSerializer, projects, request),
            "plans": _serialize(PlanSerializer, plans, request),
            "payments": _serialize(PaymentSerializer, payments, request),
            "subscriptions": _serialize(SubscriptionSerializer, subscriptions, request),
            "requests": _serialize(ServiceRequestSerializer, requests, request),
            "transactionLogs": _serialize(TransactionLogSerializer, transaction_logs, request),
        }
    )
