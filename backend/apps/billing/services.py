from datetime import datetime, timezone
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from rest_framework.exceptions import ValidationError
import stripe

from apps.clients.models import Client
from apps.core.services import audit
from apps.projects.models import Project

from .models import Payment, Plan, Subscription


stripe.api_key = settings.STRIPE_SECRET_KEY


def _stripe_ts(value):
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _decimal_from_cents(value):
    return Decimal(value or 0) / Decimal("100")


def normalize_subscription_status(status):
    allowed = {choice[0] for choice in Subscription.Status.choices}
    return status if status in allowed else Subscription.Status.PENDING


class StripeBillingService:
    @staticmethod
    def ensure_customer(client):
        if client.stripe_customer_id:
            return client.stripe_customer_id
        if not settings.STRIPE_SECRET_KEY:
            raise ValidationError("Stripe nao configurado.")
        customer = stripe.Customer.create(
            email=client.user.email,
            name=client.company_name,
            metadata={"client_id": str(client.id)},
        )
        client.stripe_customer_id = customer["id"]
        client.save(update_fields=["stripe_customer_id", "updated_at"])
        return client.stripe_customer_id

    @staticmethod
    def create_checkout_session(*, client, plan, kind, project=None, request=None):
        if kind == Payment.Kind.ONE_TIME:
            price_id = plan.stripe_setup_price_id
            mode = "payment"
        else:
            price_id = plan.stripe_monthly_price_id
            mode = "subscription"

        if not price_id:
            raise ValidationError("Plano sem price id da Stripe para este tipo de cobranca.")

        customer_id = StripeBillingService.ensure_customer(client)
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode=mode,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=settings.STRIPE_SUCCESS_URL,
            cancel_url=settings.STRIPE_CANCEL_URL,
            client_reference_id=str(client.id),
            metadata={
                "client_id": str(client.id),
                "plan_id": str(plan.id),
                "kind": kind,
                "project_id": str(project.id) if project else "",
            },
        )
        audit(client.user, "billing.checkout_session.create", request=request, target=client, metadata={"session_id": session["id"]})
        return session


class StripeWebhookService:
    @staticmethod
    @transaction.atomic
    def handle(event):
        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            return StripeWebhookService._checkout_completed(data)
        if event_type == "invoice.payment_succeeded":
            return StripeWebhookService._invoice_payment(data, Payment.Status.PAID)
        if event_type == "invoice.payment_failed":
            return StripeWebhookService._invoice_payment(data, Payment.Status.FAILED)
        if event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
            return StripeWebhookService._subscription_changed(data)
        return {"ignored": event_type}

    @staticmethod
    def _checkout_completed(session):
        metadata = session.get("metadata") or {}
        client = Client.objects.get(pk=metadata["client_id"])
        plan = Plan.objects.get(pk=metadata["plan_id"])
        project = None
        if metadata.get("project_id"):
            project = Project.objects.filter(pk=metadata["project_id"], client=client).first()

        if session.get("mode") == "subscription":
            subscription_id = session.get("subscription")
            Subscription.objects.update_or_create(
                stripe_subscription_id=subscription_id,
                defaults={
                    "client": client,
                    "plan": plan,
                    "status": Subscription.Status.PENDING,
                },
            )
        else:
            Payment.objects.update_or_create(
                stripe_payment_intent_id=session.get("payment_intent"),
                defaults={
                    "client": client,
                    "project": project,
                    "kind": Payment.Kind.ONE_TIME,
                    "status": Payment.Status.PAID,
                    "amount": _decimal_from_cents(session.get("amount_total")),
                    "currency": (session.get("currency") or "brl").upper(),
                    "paid_at": _stripe_ts(session.get("created")),
                },
            )
        return {"processed": "checkout.session.completed"}

    @staticmethod
    def _invoice_payment(invoice, status):
        subscription = None
        stripe_subscription_id = invoice.get("subscription")
        if stripe_subscription_id:
            subscription = Subscription.objects.filter(stripe_subscription_id=stripe_subscription_id).first()
            if subscription:
                subscription.status = Subscription.Status.ACTIVE if status == Payment.Status.PAID else Subscription.Status.PAST_DUE
                subscription.save(update_fields=["status", "updated_at"])

        client = subscription.client if subscription else Client.objects.filter(stripe_customer_id=invoice.get("customer")).first()
        if client:
            Payment.objects.update_or_create(
                stripe_invoice_id=invoice.get("id"),
                defaults={
                    "client": client,
                    "subscription": subscription,
                    "kind": Payment.Kind.SUBSCRIPTION,
                    "status": status,
                    "amount": _decimal_from_cents(invoice.get("amount_paid") or invoice.get("amount_due")),
                    "currency": (invoice.get("currency") or "brl").upper(),
                    "paid_at": _stripe_ts(invoice.get("status_transitions", {}).get("paid_at")) if status == Payment.Status.PAID else None,
                },
            )
        return {"processed": "invoice"}

    @staticmethod
    def _subscription_changed(stripe_subscription):
        client = Client.objects.filter(stripe_customer_id=stripe_subscription.get("customer")).first()
        if not client:
            return {"ignored": "unknown_customer"}

        plan = Plan.objects.filter(stripe_monthly_price_id=stripe_subscription["items"]["data"][0]["price"]["id"]).first()
        if not plan:
            return {"ignored": "unknown_plan"}

        status = Subscription.Status.CANCELED if stripe_subscription.get("status") == "canceled" else normalize_subscription_status(stripe_subscription.get("status"))
        Subscription.objects.update_or_create(
            stripe_subscription_id=stripe_subscription.get("id"),
            defaults={
                "client": client,
                "plan": plan,
                "status": status,
                "current_period_start": _stripe_ts(stripe_subscription.get("current_period_start")),
                "current_period_end": _stripe_ts(stripe_subscription.get("current_period_end")),
                "cancel_at_period_end": bool(stripe_subscription.get("cancel_at_period_end")),
            },
        )
        return {"processed": "subscription"}
