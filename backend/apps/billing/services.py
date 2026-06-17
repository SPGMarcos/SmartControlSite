from datetime import datetime, timezone
from decimal import Decimal
import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone as django_timezone
from rest_framework.exceptions import ValidationError
import stripe

from apps.clients.models import Client
from apps.core.services import audit
from apps.projects.models import Project

from .models import Payment, Plan, Subscription, TransactionLog


logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


def _stripe_ts(value):
    if not value:
        return None
    return datetime.fromtimestamp(value, tz=timezone.utc)


def _decimal_from_cents(value):
    return Decimal(value or 0) / Decimal("100")


def _currency(value):
    return (value or "brl").upper()


def normalize_subscription_status(status):
    allowed = {choice[0] for choice in Subscription.Status.choices}
    return status if status in allowed else Subscription.Status.PENDING


def _compact_payload(event_or_object, event_type=None):
    data_object = event_or_object.get("data", {}).get("object", {}) if event_or_object.get("data") else event_or_object
    return {
        "id": event_or_object.get("id"),
        "type": event_type or event_or_object.get("type") or data_object.get("object"),
        "livemode": event_or_object.get("livemode"),
        "object_id": data_object.get("id"),
        "object": data_object.get("object"),
        "customer": data_object.get("customer"),
        "subscription": data_object.get("subscription"),
        "payment_intent": data_object.get("payment_intent"),
        "amount_total": data_object.get("amount_total"),
        "amount_paid": data_object.get("amount_paid"),
        "amount_due": data_object.get("amount_due"),
        "currency": data_object.get("currency"),
        "metadata": dict(data_object.get("metadata") or {}),
    }


def _project_from_metadata(metadata, client=None):
    project_id = metadata.get("project_id")
    if not project_id:
        return None
    queryset = Project.objects.all()
    if client:
        queryset = queryset.filter(client=client)
    return queryset.filter(pk=project_id).first()


def _touch_project_status(project, status):
    if not project or project.status == Project.Status.COMPLETED:
        return
    if project.status != status:
        project.status = status
        project.save(update_fields=["status", "updated_at"])


def _payment_amount(plan, kind):
    if kind == Payment.Kind.SUBSCRIPTION:
        return plan.monthly_price
    return plan.setup_price


def _stripe_line_item(plan, kind):
    if kind == Payment.Kind.SUBSCRIPTION:
        price_id = plan.stripe_monthly_price_id
        amount = plan.monthly_price
        recurring = True
    else:
        price_id = plan.stripe_setup_price_id
        amount = plan.setup_price
        recurring = False

    if price_id:
        return {"price": price_id, "quantity": 1}
    if amount <= 0:
        raise ValidationError("Plano sem valor configurado para este tipo de cobranca.")

    price_data = {
        "currency": "brl",
        "unit_amount": int(amount * Decimal("100")),
        "product_data": {
            "name": f"{plan.name} - {'assinatura mensal' if recurring else 'projeto unico'}",
            "metadata": {"plan_id": str(plan.id), "plan_slug": plan.slug},
        },
    }
    if recurring:
        price_data["recurring"] = {"interval": "month"}
    return {"price_data": price_data, "quantity": 1}


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
    @transaction.atomic
    def create_checkout_session(*, client, plan, kind, project=None, request=None, installments=None):
        if not settings.STRIPE_SECRET_KEY:
            raise ValidationError("Stripe nao configurado.")

        if kind == Payment.Kind.SUBSCRIPTION:
            mode = "subscription"
        else:
            mode = "payment"

        metadata = {
            "client_id": str(client.id),
            "plan_id": str(plan.id),
            "kind": kind,
            "project_id": str(project.id) if project else "",
            "installments": str(installments or ""),
        }
        customer_id = StripeBillingService.ensure_customer(client)
        session_payload = {
            "customer": customer_id,
            "mode": mode,
            "line_items": [_stripe_line_item(plan, kind)],
            "success_url": settings.STRIPE_SUCCESS_URL,
            "cancel_url": settings.STRIPE_CANCEL_URL,
            "client_reference_id": str(client.id),
            "metadata": metadata,
            "payment_method_types": ["card"],
            "billing_address_collection": "required",
            "allow_promotion_codes": True,
            "locale": "pt-BR",
            "customer_update": {"address": "auto", "name": "auto"},
        }

        if mode == "subscription":
            session_payload["subscription_data"] = {"metadata": metadata}
        else:
            session_payload["payment_intent_data"] = {"metadata": metadata}
            session_payload["invoice_creation"] = {"enabled": True}
            if kind == Payment.Kind.INSTALLMENT:
                session_payload["payment_method_options"] = {"card": {"installments": {"enabled": True}}}

        session = stripe.checkout.Session.create(**session_payload)
        amount = _payment_amount(plan, kind)
        payment = None
        if mode == "payment":
            payment = Payment.objects.create(
                client=client,
                user=client.user,
                project=project,
                kind=kind,
                status=Payment.Status.PENDING,
                amount=amount,
                currency="BRL",
                stripe_checkout_session_id=session["id"],
                stripe_payment_intent=session.get("payment_intent"),
                metadata={"plan_id": plan.id, "installments": installments or None},
            )
            _touch_project_status(project, Project.Status.PAYMENT_PENDING)

        TransactionLog.objects.create(
            event_type="checkout.session.created",
            status=TransactionLog.Status.PROCESSED,
            client=client,
            project=project,
            payment=payment,
            amount=amount,
            currency="BRL",
            payload={"session_id": session["id"], "mode": mode, "kind": kind, "plan_id": plan.id},
        )
        audit(client.user, "billing.checkout_session.create", request=request, target=client, metadata={"session_id": session["id"], "kind": kind})
        return session

    @staticmethod
    def create_portal_session(*, client, request=None):
        if not settings.STRIPE_SECRET_KEY:
            raise ValidationError("Stripe nao configurado.")
        customer_id = StripeBillingService.ensure_customer(client)
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=settings.STRIPE_PORTAL_RETURN_URL,
        )
        TransactionLog.objects.create(
            event_type="billing_portal.session.created",
            status=TransactionLog.Status.PROCESSED,
            client=client,
            payload={"session_id": session["id"]},
        )
        audit(client.user, "billing.portal_session.create", request=request, target=client, metadata={"session_id": session["id"]})
        return session


class StripeWebhookService:
    @staticmethod
    def handle(event):
        event_id = event.get("id")
        event_type = event.get("type")
        log, created = TransactionLog.objects.get_or_create(
            stripe_event_id=event_id,
            defaults={
                "event_type": event_type,
                "status": TransactionLog.Status.CREATED,
                "payload": _compact_payload(event, event_type),
            },
        )
        if not created:
            return {"duplicate": event_id}

        try:
            with transaction.atomic():
                result = StripeWebhookService._dispatch(event)
                log.status = TransactionLog.Status.PROCESSED if result.get("processed") else TransactionLog.Status.IGNORED
                for field in ("client", "subscription", "project", "payment", "amount", "currency"):
                    value = result.get(field)
                    if value is not None:
                        setattr(log, field, value)
                log.payload = {**log.payload, "result": {key: str(value) for key, value in result.items() if key not in {"client", "subscription", "project", "payment"}}}
                log.save()
                return {key: str(value) for key, value in result.items() if key not in {"client", "subscription", "project", "payment"}}
        except Exception as exc:
            log.status = TransactionLog.Status.FAILED
            log.payload = {**log.payload, "error": str(exc)[:500]}
            log.save(update_fields=["status", "payload", "updated_at"])
            logger.exception("Stripe webhook processing failed: %s", event_type)
            raise

    @staticmethod
    def _dispatch(event):
        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "checkout.session.completed":
            return StripeWebhookService._checkout_completed(data)
        if event_type == "checkout.session.expired":
            return StripeWebhookService._checkout_expired(data)
        if event_type == "payment_intent.succeeded":
            return StripeWebhookService._payment_intent(data, Payment.Status.PAID)
        if event_type == "payment_intent.payment_failed":
            return StripeWebhookService._payment_intent(data, Payment.Status.FAILED)
        if event_type in {"invoice.paid", "invoice.payment_succeeded"}:
            return StripeWebhookService._invoice_payment(data, Payment.Status.PAID)
        if event_type == "invoice.payment_failed":
            return StripeWebhookService._invoice_payment(data, Payment.Status.FAILED)
        if event_type in {"customer.subscription.created", "customer.subscription.updated", "customer.subscription.deleted"}:
            return StripeWebhookService._subscription_changed(data)
        if event_type == "charge.refunded":
            return StripeWebhookService._charge_refunded(data)
        return {"ignored": event_type}

    @staticmethod
    def _checkout_completed(session):
        metadata = session.get("metadata") or {}
        client = Client.objects.filter(pk=metadata.get("client_id")).first() or Client.objects.filter(stripe_customer_id=session.get("customer")).first()
        if not client:
            return {"ignored": "unknown_client"}

        plan = Plan.objects.filter(pk=metadata.get("plan_id")).first()
        if not plan:
            return {"ignored": "unknown_plan", "client": client}

        project = _project_from_metadata(metadata, client)
        if session.get("mode") == "subscription":
            subscription_id = session.get("subscription")
            subscription, _ = Subscription.objects.update_or_create(
                stripe_subscription_id=subscription_id,
                defaults={
                    "client": client,
                    "user": client.user,
                    "plan": plan,
                    "project": project,
                    "status": Subscription.Status.PENDING,
                    "plano": plan.slug or plan.name,
                    "stripe_customer_id": session.get("customer") or client.stripe_customer_id,
                },
            )
            return {"processed": "checkout.session.completed", "client": client, "project": project, "subscription": subscription}

        payment_status = Payment.Status.PAID if session.get("payment_status") == "paid" else Payment.Status.PENDING
        payment = StripeWebhookService._upsert_payment_from_checkout(session, client, plan, project, payment_status)
        if payment.status == Payment.Status.PAID:
            _touch_project_status(project, Project.Status.IN_DEVELOPMENT)
        return {
            "processed": "checkout.session.completed",
            "client": client,
            "project": project,
            "payment": payment,
            "amount": payment.amount,
            "currency": payment.currency,
        }

    @staticmethod
    def _checkout_expired(session):
        payment = Payment.objects.filter(stripe_checkout_session_id=session.get("id")).first()
        if not payment:
            return {"ignored": "unknown_checkout_session"}
        payment.status = Payment.Status.CANCELED
        payment.save(update_fields=["status", "updated_at"])
        _touch_project_status(payment.project, Project.Status.PAYMENT_PENDING)
        return {"processed": "checkout.session.expired", "client": payment.client, "project": payment.project, "payment": payment}

    @staticmethod
    def _payment_intent(payment_intent, status):
        metadata = payment_intent.get("metadata") or {}
        payment = Payment.objects.filter(stripe_payment_intent_id=payment_intent.get("id")).first()
        client = payment.client if payment else Client.objects.filter(pk=metadata.get("client_id")).first()
        if not client:
            return {"ignored": "unknown_client"}

        plan = Plan.objects.filter(pk=metadata.get("plan_id")).first()
        project = payment.project if payment else _project_from_metadata(metadata, client)
        if not payment:
            payment = Payment.objects.create(
                client=client,
                user=client.user,
                project=project,
                kind=metadata.get("kind") or Payment.Kind.ONE_TIME,
                amount=_decimal_from_cents(payment_intent.get("amount_received") or payment_intent.get("amount")),
                currency=_currency(payment_intent.get("currency")),
                stripe_payment_intent_id=payment_intent.get("id"),
                stripe_payment_intent=payment_intent.get("id"),
                metadata={"plan_id": plan.id if plan else None},
            )

        payment.status = status
        payment.stripe_payment_intent_id = payment_intent.get("id")
        payment.stripe_payment_intent = payment_intent.get("id")
        payment.amount = _decimal_from_cents(payment_intent.get("amount_received") or payment_intent.get("amount"))
        payment.currency = _currency(payment_intent.get("currency"))
        payment.paid_at = django_timezone.now() if status == Payment.Status.PAID else None
        payment.save(update_fields=["status", "stripe_payment_intent_id", "stripe_payment_intent", "amount", "currency", "paid_at", "updated_at"])

        _touch_project_status(project, Project.Status.IN_DEVELOPMENT if status == Payment.Status.PAID else Project.Status.PAYMENT_PENDING)
        return {"processed": "payment_intent", "client": client, "project": project, "payment": payment, "amount": payment.amount, "currency": payment.currency}

    @staticmethod
    def _invoice_payment(invoice, status):
        subscription = None
        stripe_subscription_id = invoice.get("subscription")
        if stripe_subscription_id:
            subscription = Subscription.objects.filter(stripe_subscription_id=stripe_subscription_id).select_related("client", "project").first()
            if subscription:
                subscription.status = Subscription.Status.ACTIVE if status == Payment.Status.PAID else Subscription.Status.PAST_DUE
                subscription.save(update_fields=["status", "updated_at"])

        client = subscription.client if subscription else Client.objects.filter(stripe_customer_id=invoice.get("customer")).first()
        if not client:
            return {"ignored": "unknown_client"}

        project = subscription.project if subscription else None
        payment, _ = Payment.objects.update_or_create(
            stripe_invoice_id=invoice.get("id"),
            defaults={
                "client": client,
                "user": client.user,
                "subscription": subscription,
                "project": project,
                "kind": Payment.Kind.SUBSCRIPTION,
                "status": status,
                "amount": _decimal_from_cents(invoice.get("amount_paid") or invoice.get("amount_due")),
                "currency": _currency(invoice.get("currency")),
                "paid_at": _stripe_ts(invoice.get("status_transitions", {}).get("paid_at")) if status == Payment.Status.PAID else None,
            },
        )
        _touch_project_status(project, Project.Status.IN_DEVELOPMENT if status == Payment.Status.PAID else Project.Status.PAYMENT_PENDING)
        return {"processed": "invoice", "client": client, "subscription": subscription, "project": project, "payment": payment, "amount": payment.amount, "currency": payment.currency}

    @staticmethod
    def _subscription_changed(stripe_subscription):
        metadata = stripe_subscription.get("metadata") or {}
        client = Client.objects.filter(stripe_customer_id=stripe_subscription.get("customer")).first() or Client.objects.filter(pk=metadata.get("client_id")).first()
        if not client:
            return {"ignored": "unknown_customer"}

        items = stripe_subscription.get("items", {}).get("data", [])
        price_id = items[0]["price"]["id"] if items else ""
        plan = Plan.objects.filter(stripe_monthly_price_id=price_id).first() or Plan.objects.filter(pk=metadata.get("plan_id")).first()
        if not plan:
            return {"ignored": "unknown_plan", "client": client}

        existing_subscription = Subscription.objects.filter(stripe_subscription_id=stripe_subscription.get("id")).select_related("project").first()
        project = _project_from_metadata(metadata, client) or (existing_subscription.project if existing_subscription else None)
        status = Subscription.Status.CANCELED if stripe_subscription.get("status") == "canceled" else normalize_subscription_status(stripe_subscription.get("status"))
        subscription, _ = Subscription.objects.update_or_create(
            stripe_subscription_id=stripe_subscription.get("id"),
            defaults={
                "client": client,
                "user": client.user,
                "plan": plan,
                "project": project,
                "status": status,
                "plano": plan.slug or plan.name,
                "stripe_customer_id": stripe_subscription.get("customer") or client.stripe_customer_id,
                "current_period_start": _stripe_ts(stripe_subscription.get("current_period_start")),
                "current_period_end": _stripe_ts(stripe_subscription.get("current_period_end")),
                "cancel_at_period_end": bool(stripe_subscription.get("cancel_at_period_end")),
            },
        )
        return {"processed": "subscription", "client": client, "project": project, "subscription": subscription}

    @staticmethod
    def _charge_refunded(charge):
        payment = Payment.objects.filter(stripe_payment_intent_id=charge.get("payment_intent")).first()
        if not payment:
            return {"ignored": "unknown_payment"}
        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=["status", "updated_at"])
        _touch_project_status(payment.project, Project.Status.PAYMENT_PENDING)
        return {"processed": "refund", "client": payment.client, "project": payment.project, "payment": payment}

    @staticmethod
    def _upsert_payment_from_checkout(session, client, plan, project, status):
        payment = Payment.objects.filter(stripe_checkout_session_id=session.get("id")).first()
        if not payment and session.get("payment_intent"):
            payment = Payment.objects.filter(stripe_payment_intent_id=session.get("payment_intent")).first()

        values = {
            "client": client,
            "user": client.user,
            "project": project,
            "kind": session.get("metadata", {}).get("kind") or Payment.Kind.ONE_TIME,
            "status": status,
            "amount": _decimal_from_cents(session.get("amount_total")) or plan.setup_price,
            "currency": _currency(session.get("currency")),
            "stripe_checkout_session_id": session.get("id"),
            "stripe_payment_intent_id": session.get("payment_intent"),
            "stripe_payment_intent": session.get("payment_intent"),
            "paid_at": _stripe_ts(session.get("created")) if status == Payment.Status.PAID else None,
            "metadata": {"plan_id": plan.id},
        }

        if payment:
            for key, value in values.items():
                setattr(payment, key, value)
            payment.save()
            return payment
        return Payment.objects.create(**values)
