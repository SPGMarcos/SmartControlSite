from types import SimpleNamespace

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.core.permissions import IsAdmin
from apps.core.views import admin_status
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
