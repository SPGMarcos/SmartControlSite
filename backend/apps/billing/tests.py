from django.test import TestCase
from rest_framework.exceptions import ValidationError

from apps.billing.models import Payment
from apps.billing.services import StripeWebhookService
from apps.billing.views import get_or_create_billing_client
from apps.clients.models import Client
from apps.users.models import User


class BillingClientPermissionTests(TestCase):
    def test_admin_can_get_billing_client_for_checkout(self):
        user = User.objects.create_user(
            email="mgfm554@gmail.com",
            password="test-pass",
            first_name="Marcos",
            role=User.Role.ADMIN,
        )

        client = get_or_create_billing_client(user)

        self.assertEqual(client.user, user)
        self.assertEqual(client.company_name, "Marcos")
        self.assertEqual(Client.objects.count(), 1)

    def test_client_can_get_billing_client_for_checkout(self):
        user = User.objects.create_user(
            email="cliente@example.com",
            password="test-pass",
            role=User.Role.CLIENT,
        )

        client = get_or_create_billing_client(user)

        self.assertEqual(client.user, user)
        self.assertEqual(client.company_name, "cliente@example.com")

    def test_unexpected_role_cannot_get_billing_client_for_checkout(self):
        user = User.objects.create_user(
            email="operador@example.com",
            password="test-pass",
            role="operator",
        )

        with self.assertRaises(ValidationError):
            get_or_create_billing_client(user)


class StripeRefundSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="cliente@example.com", password="test-pass", role=User.Role.CLIENT)
        self.client = Client.objects.create(user=self.user, company_name="Cliente", stripe_customer_id="cus_test")

    def test_refund_matches_payment_by_payment_intent(self):
        payment = Payment.objects.create(
            client=self.client,
            user=self.user,
            kind=Payment.Kind.ONE_TIME,
            status=Payment.Status.PAID,
            amount="799.00",
            currency="BRL",
            stripe_payment_intent_id="pi_test",
        )

        result = StripeWebhookService._charge_refunded(
            {
                "id": "ch_test",
                "payment_intent": "pi_test",
                "customer": "cus_test",
                "amount": 79900,
                "amount_refunded": 79900,
                "currency": "brl",
            }
        )

        payment.refresh_from_db()
        self.assertEqual(result["processed"], "refund")
        self.assertEqual(payment.status, Payment.Status.REFUNDED)
        self.assertEqual(payment.metadata["stripe_refund"]["charge_id"], "ch_test")

    def test_refund_matches_subscription_payment_by_invoice(self):
        payment = Payment.objects.create(
            client=self.client,
            user=self.user,
            kind=Payment.Kind.SUBSCRIPTION,
            status=Payment.Status.PAID,
            amount="898.00",
            currency="BRL",
            stripe_invoice_id="in_test",
        )

        result = StripeWebhookService._charge_refunded(
            {
                "id": "ch_test",
                "invoice": "in_test",
                "customer": "cus_test",
                "amount": 89800,
                "amount_refunded": 89800,
                "currency": "brl",
            }
        )

        payment.refresh_from_db()
        self.assertEqual(result["processed"], "refund")
        self.assertEqual(payment.status, Payment.Status.REFUNDED)

    def test_refund_matches_subscription_payment_by_customer_and_amount_when_invoice_is_missing(self):
        payment = Payment.objects.create(
            client=self.client,
            user=self.user,
            kind=Payment.Kind.SUBSCRIPTION,
            status=Payment.Status.PAID,
            amount="898.00",
            currency="BRL",
        )

        result = StripeWebhookService._charge_refunded(
            {
                "id": "ch_test",
                "customer": "cus_test",
                "amount": 89800,
                "amount_refunded": 89800,
                "currency": "brl",
            }
        )

        payment.refresh_from_db()
        self.assertEqual(result["processed"], "refund")
        self.assertEqual(payment.status, Payment.Status.REFUNDED)

    def test_refund_does_not_guess_when_multiple_payments_match(self):
        for _ in range(2):
            Payment.objects.create(
                client=self.client,
                user=self.user,
                kind=Payment.Kind.SUBSCRIPTION,
                status=Payment.Status.PAID,
                amount="898.00",
                currency="BRL",
            )

        result = StripeWebhookService._charge_refunded(
            {
                "id": "ch_test",
                "customer": "cus_test",
                "amount": 89800,
                "amount_refunded": 89800,
                "currency": "brl",
            }
        )

        self.assertEqual(result["ignored"], "ambiguous_refunded_payment")
        self.assertEqual(Payment.objects.filter(status=Payment.Status.REFUNDED).count(), 0)

    def test_paid_invoice_sync_does_not_restore_refunded_payment(self):
        payment = Payment.objects.create(
            client=self.client,
            user=self.user,
            kind=Payment.Kind.SUBSCRIPTION,
            status=Payment.Status.REFUNDED,
            amount="898.00",
            currency="BRL",
            stripe_invoice_id="in_test",
        )

        StripeWebhookService._invoice_payment(
            {
                "id": "in_test",
                "customer": "cus_test",
                "status": "paid",
                "paid": True,
                "amount_paid": 89800,
                "currency": "brl",
                "status_transitions": {"paid_at": 1786552712},
            },
            Payment.Status.PAID,
        )

        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.REFUNDED)
