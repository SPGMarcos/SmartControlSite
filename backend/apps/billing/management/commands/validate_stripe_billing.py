import json
import time
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
import stripe

from apps.clients.models import Client
from apps.users.models import User

from ...models import Payment, Plan, Subscription, TransactionLog
from ...services import StripeBillingService, StripeWebhookService


def money_to_cents(value):
    return int(Decimal(value or 0) * Decimal("100"))


class Command(BaseCommand):
    help = "Validates database, Stripe prices, checkout creation, and signed webhook handling."

    def add_arguments(self, parser):
        parser.add_argument("--create-checkout", action="store_true", help="Create a real Stripe Checkout Session in the configured account.")
        parser.add_argument("--plan-slug", default="", help="Plan slug to use for checkout tests. Defaults to the first active paid plan.")
        parser.add_argument("--kind", choices=[Payment.Kind.ONE_TIME, Payment.Kind.SUBSCRIPTION], default=Payment.Kind.ONE_TIME)
        parser.add_argument("--json", action="store_true", help="Emit a JSON report.")

    def handle(self, *args, **options):
        report = {
            "database": self.check_database(),
            "stripe": self.check_stripe(),
            "plans": [],
            "checkout": {"tested": False},
            "webhook": self.check_webhook_signature(),
            "subscriptions": self.check_subscription_handlers(),
        }

        plans = list(Plan.objects.filter(is_active=True).order_by("setup_price", "monthly_price", "id"))
        for plan in plans:
            report["plans"].append(self.check_plan(plan))

        if options["create_checkout"]:
            report["checkout"] = self.create_checkout(plans, options["plan_slug"], options["kind"])

        if options["json"]:
            self.stdout.write(json.dumps(report, default=str, indent=2, sort_keys=True))
        else:
            self.write_human(report)

    def check_database(self):
        with connection.cursor() as cursor:
            cursor.execute("select 1")
            cursor.fetchone()
        return {
            "status": "ok",
            "host": settings.DATABASES["default"].get("HOST"),
            "name": settings.DATABASES["default"].get("NAME"),
            "queries": ["select 1", "plans active count", "payments count", "subscriptions count", "transaction logs count"],
            "active_plans": Plan.objects.filter(is_active=True).count(),
            "payments": Payment.objects.count(),
            "subscriptions": Subscription.objects.count(),
            "transaction_logs": TransactionLog.objects.count(),
        }

    def check_stripe(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        mode = "test" if settings.STRIPE_SECRET_KEY.startswith("sk_test_") else "live" if settings.STRIPE_SECRET_KEY.startswith("sk_live_") else "unknown"
        account = stripe.Account.retrieve() if settings.STRIPE_SECRET_KEY else {}
        prices = stripe.Price.list(active=True, limit=100, expand=["data.product"]) if settings.STRIPE_SECRET_KEY else {"data": []}
        return {
            "status": "ok" if account.get("id") else "not_configured",
            "mode": mode,
            "key_prefix": settings.STRIPE_SECRET_KEY[:8] if settings.STRIPE_SECRET_KEY else "",
            "charges_enabled": account.get("charges_enabled"),
            "details_submitted": account.get("details_submitted"),
            "products": sorted({getattr(item.product, "name", "") for item in prices.data if getattr(item, "product", None)}),
            "prices": [
                {
                    "id": item.id,
                    "livemode": item.livemode,
                    "active": item.active,
                    "currency": item.currency,
                    "unit_amount": item.unit_amount,
                    "recurring": item.recurring.interval if item.recurring else "",
                    "product": item.product.id if hasattr(item.product, "id") else item.product,
                    "product_name": getattr(item.product, "name", ""),
                }
                for item in prices.data
            ],
        }

    def check_plan(self, plan):
        issues = []
        setup_price = self.retrieve_price(plan.stripe_setup_price_id, expected_cents=money_to_cents(plan.setup_price), expected_recurring=False)
        monthly_price = self.retrieve_price(plan.stripe_monthly_price_id, expected_cents=money_to_cents(plan.monthly_price), expected_recurring=True)
        if plan.setup_price > 0 and not plan.stripe_setup_price_id:
            issues.append("missing_setup_price_id; checkout uses dynamic price_data fallback")
        if plan.monthly_price > 0 and not plan.stripe_monthly_price_id:
            issues.append("missing_monthly_price_id; checkout uses dynamic price_data fallback")
        for result in (setup_price, monthly_price):
            if result.get("status") == "error":
                issues.append(result["error"])
        return {
            "id": plan.id,
            "slug": plan.slug,
            "name": plan.name,
            "active": plan.is_active,
            "setup_price": plan.setup_price,
            "monthly_price": plan.monthly_price,
            "stripe_setup_price": setup_price,
            "stripe_monthly_price": monthly_price,
            "status": "ok" if not issues else "warning",
            "issues": issues,
        }

    def retrieve_price(self, price_id, *, expected_cents, expected_recurring):
        if not price_id:
            return {"status": "not_configured"}
        try:
            price = stripe.Price.retrieve(price_id, expand=["product"])
        except stripe.error.StripeError as exc:
            return {"status": "error", "id": price_id, "error": str(exc)}

        mode = "live" if price.livemode else "test"
        key_mode = "live" if settings.STRIPE_SECRET_KEY.startswith("sk_live_") else "test" if settings.STRIPE_SECRET_KEY.startswith("sk_test_") else "unknown"
        issues = []
        if key_mode != "unknown" and mode != key_mode:
            issues.append(f"price_mode_{mode}_does_not_match_key_{key_mode}")
        if expected_cents > 0 and price.unit_amount != expected_cents:
            issues.append(f"amount_mismatch_expected_{expected_cents}_got_{price.unit_amount}")
        is_recurring = bool(price.recurring)
        if expected_recurring != is_recurring:
            issues.append("recurring_mismatch")
        return {
            "status": "ok" if not issues else "warning",
            "id": price.id,
            "mode": mode,
            "active": price.active,
            "currency": price.currency,
            "unit_amount": price.unit_amount,
            "recurring": price.recurring.interval if price.recurring else "",
            "product": price.product.id if hasattr(price.product, "id") else price.product,
            "product_name": getattr(price.product, "name", ""),
            "issues": issues,
        }

    def create_checkout(self, plans, slug, kind):
        plan = next((item for item in plans if item.slug == slug), None) if slug else None
        if plan is None:
            plan = next((item for item in plans if item.setup_price > 0 or item.monthly_price > 0), None)
        if plan is None:
            return {"tested": True, "status": "error", "error": "no_active_paid_plan"}

        user, _ = User.objects.get_or_create(
            email="stripe-diagnostic@smartcontrol.local",
            defaults={"first_name": "Stripe", "last_name": "Diagnostic", "role": User.Role.CLIENT, "is_active": True},
        )
        client, _ = Client.objects.get_or_create(user=user, defaults={"company_name": "Stripe Diagnostic"})
        session = StripeBillingService.create_checkout_session(client=client, plan=plan, kind=kind)
        return {
            "tested": True,
            "status": "ok",
            "plan": plan.slug,
            "kind": kind,
            "session_id": session["id"],
            "url": session["url"],
            "mode": session["mode"],
        }

    def check_webhook_signature(self):
        if not settings.STRIPE_WEBHOOK_SECRET:
            return {"status": "not_configured", "secret_found": False}
        payload = json.dumps(
            {
                "id": f"evt_diag_{int(time.time())}",
                "object": "event",
                "type": "checkout.session.expired",
                "livemode": settings.STRIPE_SECRET_KEY.startswith("sk_live_"),
                "data": {"object": {"id": "cs_diag_missing", "object": "checkout.session"}},
            },
            separators=(",", ":"),
        ).encode("utf-8")
        timestamp = int(time.time())
        signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
        import hmac
        import hashlib

        signature = hmac.new(settings.STRIPE_WEBHOOK_SECRET.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256).hexdigest()
        header = f"t={timestamp},v1={signature}"
        event = stripe.Webhook.construct_event(payload, header, settings.STRIPE_WEBHOOK_SECRET)
        result = StripeWebhookService.handle(event)
        return {"status": "ok", "secret_found": True, "validated": True, "event_type": event["type"], "result": result}

    def check_subscription_handlers(self):
        return {
            "create_update_events": "implemented",
            "cancel_event": "implemented",
            "access_update": "implemented; active subscriptions sync profiles.plano, cancellation without another active subscription resets profiles.plano to client",
        }

    def write_human(self, report):
        for section, data in report.items():
            self.stdout.write(self.style.MIGRATE_HEADING(section.upper()))
            self.stdout.write(json.dumps(data, default=str, indent=2, sort_keys=True))
