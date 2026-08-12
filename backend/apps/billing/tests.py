from django.test import TestCase
from rest_framework.exceptions import ValidationError

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
