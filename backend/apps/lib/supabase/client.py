import requests
from django.conf import settings
from rest_framework.exceptions import APIException, ValidationError


class SupabaseConfigurationError(APIException):
    status_code = 503
    default_detail = "Supabase nao configurado."


class SupabaseAuthClient:
    def __init__(self):
        self.base_url = settings.SUPABASE_URL
        self.anon_key = settings.SUPABASE_ANON_KEY
        self.service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY

    def _require(self, admin=False):
        if not self.base_url or not self.anon_key or (admin and not self.service_role_key):
            raise SupabaseConfigurationError()

    def _headers(self, admin=False, access_token=None):
        key = self.service_role_key if admin else self.anon_key
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {access_token or key}",
            "Content-Type": "application/json",
        }
        return headers

    def _request(self, method, path, *, payload=None, admin=False, access_token=None):
        self._require(admin=admin)
        response = requests.request(
            method,
            f"{self.base_url}/auth/v1{path}",
            headers=self._headers(admin=admin, access_token=access_token),
            json=payload or {},
            timeout=15,
        )
        data = response.json() if response.content else {}
        if response.status_code >= 400:
            message = data.get("msg") or data.get("message") or data.get("error_description") or "Erro no Supabase Auth."
            raise ValidationError(message)
        return data

    def create_user(self, *, email, password, metadata=None):
        return self._request(
            "POST",
            "/admin/users",
            admin=True,
            payload={
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": metadata or {},
            },
        )

    def sign_in_with_password(self, *, email, password):
        return self._request(
            "POST",
            "/token?grant_type=password",
            payload={"email": email, "password": password},
        )

    def refresh_session(self, *, refresh_token):
        return self._request(
            "POST",
            "/token?grant_type=refresh_token",
            payload={"refresh_token": refresh_token},
        )

    def sign_out(self, *, access_token):
        if not access_token:
            return {}
        return self._request("POST", "/logout", access_token=access_token)

    def request_password_reset(self, *, email):
        payload = {"email": email}
        redirect = settings.SUPABASE_PASSWORD_RESET_REDIRECT_URL or f"{settings.FRONTEND_URL}/reset-password"
        if redirect:
            payload["redirect_to"] = redirect
        return self._request("POST", "/recover", payload=payload)

    def update_password(self, *, access_token, new_password):
        return self._request("PUT", "/user", access_token=access_token, payload={"password": new_password})
