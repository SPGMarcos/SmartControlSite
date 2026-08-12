from types import SimpleNamespace
from decimal import Decimal

from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.billing.models import Payment, Plan, Subscription
from apps.clients.models import Client
from apps.core.permissions import IsAdmin
from apps.core.views import admin_dashboard, admin_status
from apps.projects.models import Project, ServiceRequest
from apps.users.models import User
from apps.users.roles import is_primary_admin_email, resolved_role_for_user


class AdminRoleTests(SimpleTestCase):
    @override_settings(PRIMARY_ADMIN_EMAILS=["mgfm554@gmail.com"])
    def test_primary_admin_email_resolves_to_admin_role(self):
        self.assertTrue(is_primary_admin_email("MGFM554@gmail.com"))
        self.assertEqual(resolved_role_for_user("mgfm554@gmail.com", "client"), "admin")

    @override_settings(PRIMARY_ADMIN_EMAILS=["mgfm554@gmail.com"])
    def test_common_email_does_not_resolve_to_admin_role(self):
        self.assertFalse(is_primary_admin_email("cliente@example.com"))
        self.assertEqual(resolved_role_for_user("cliente@example.com", "client"), "client")


class AdminPermissionTests(SimpleTestCase):
    def test_is_admin_allows_only_authenticated_admin_users(self):
        permission = IsAdmin()
        admin_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role="admin"))
        client_request = SimpleNamespace(user=SimpleNamespace(is_authenticated=True, role="client"))

        self.assertTrue(permission.has_permission(admin_request, None))
        self.assertFalse(permission.has_permission(client_request, None))

    def test_admin_status_blocks_common_user(self):
        request = APIRequestFactory().get("/api/admin/status/")
        user = SimpleNamespace(id=1, pk=1, email="cliente@example.com", role="client", is_authenticated=True)
        force_authenticate(request, user=user)

        response = admin_status(request)

        self.assertEqual(response.status_code, 403)

    def test_admin_status_allows_admin_user(self):
        request = APIRequestFactory().get("/api/admin/status/")
        user = SimpleNamespace(id=1, pk=1, email="mgfm554@gmail.com", role="admin", is_authenticated=True)
        force_authenticate(request, user=user)

        response = admin_status(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["admin"])
        self.assertEqual(response.data["user"]["email"], "mgfm554@gmail.com")


class AdminDashboardSnapshotTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.admin = User.objects.create_user(email="mgfm554@gmail.com", password="test-pass", role=User.Role.ADMIN)
        self.user = User.objects.create_user(email="cliente@example.com", password="test-pass", role=User.Role.CLIENT)
        self.client = Client.objects.create(user=self.user, company_name="Cliente")
        self.plan = Plan.objects.create(name="Pro", slug="pro", setup_price="999.00", monthly_price="199.00")

    def test_admin_dashboard_blocks_common_user(self):
        request = self.factory.get("/api/admin/dashboard/")
        force_authenticate(request, user=self.user)

        response = admin_dashboard(request)

        self.assertEqual(response.status_code, 403)

    @override_settings(STRIPE_SECRET_KEY="")
    def test_admin_dashboard_returns_synced_metrics_without_false_revenue(self):
        project = Project.objects.create(
            client=self.client,
            plan=self.plan,
            name="Site Cliente",
            site_type=Project.SiteType.LANDING_PAGE,
            status=Project.Status.IN_DEVELOPMENT,
        )
        subscription = Subscription.objects.create(
            client=self.client,
            user=self.user,
            plan=self.plan,
            project=project,
            status=Subscription.Status.ACTIVE,
            stripe_subscription_id="sub_test",
        )
        Payment.objects.create(
            client=self.client,
            user=self.user,
            project=project,
            kind=Payment.Kind.ONE_TIME,
            status=Payment.Status.PAID,
            amount="999.00",
            currency="BRL",
        )
        Payment.objects.create(
            client=self.client,
            user=self.user,
            subscription=subscription,
            project=project,
            kind=Payment.Kind.SUBSCRIPTION,
            status=Payment.Status.PAID,
            amount="199.00",
            currency="BRL",
        )
        Payment.objects.create(
            client=self.client,
            user=self.user,
            subscription=subscription,
            project=project,
            kind=Payment.Kind.SUBSCRIPTION,
            status=Payment.Status.REFUNDED,
            amount="199.00",
            currency="BRL",
        )
        ServiceRequest.objects.create(
            project=project,
            client=self.client,
            created_by=self.user,
            title="Ajuste",
            description="Precisa de ajuste",
            status=ServiceRequest.Status.OPEN,
        )

        request = self.factory.get("/api/admin/dashboard/")
        force_authenticate(request, user=self.admin)

        response = admin_dashboard(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["metrics"]["paidSales"], 2)
        self.assertEqual(response.data["metrics"]["paymentsTotal"], 3)
        self.assertEqual(Decimal(response.data["metrics"]["revenue"]), Decimal("1198.00"))
        self.assertEqual(response.data["metrics"]["activeSubscriptions"], 1)
        self.assertEqual(response.data["metrics"]["soldSites"], 1)
        self.assertEqual(response.data["metrics"]["openSupportRequests"], 1)

    @override_settings(STRIPE_SECRET_KEY="")
    def test_admin_dashboard_counts_only_latest_paid_subscription_per_client(self):
        old_plan = Plan.objects.create(name="Old", slug="old", setup_price="799.00", monthly_price="99.00")
        old_subscription = Subscription.objects.create(
            client=self.client,
            user=self.user,
            plan=old_plan,
            status=Subscription.Status.ACTIVE,
            stripe_subscription_id="sub_old",
        )
        new_subscription = Subscription.objects.create(
            client=self.client,
            user=self.user,
            plan=self.plan,
            status=Subscription.Status.ACTIVE,
            stripe_subscription_id="sub_new",
        )
        Payment.objects.create(
            client=self.client,
            user=self.user,
            subscription=old_subscription,
            kind=Payment.Kind.SUBSCRIPTION,
            status=Payment.Status.REFUNDED,
            amount="99.00",
            currency="BRL",
        )
        Payment.objects.create(
            client=self.client,
            user=self.user,
            kind=Payment.Kind.SUBSCRIPTION,
            status=Payment.Status.PAID,
            amount="199.00",
            currency="BRL",
        )

        request = self.factory.get("/api/admin/dashboard/")
        force_authenticate(request, user=self.admin)

        response = admin_dashboard(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["metrics"]["activeSubscriptions"], 1)
        self.assertEqual(response.data["metrics"]["subscriptionsTotal"], 2)
