import logging

from apps.core.services import get_client_ip
from apps.lib.supabase.client import SupabaseAuthClient

from .models import AuthLog

logger = logging.getLogger(__name__)


class AuthLogService:
    @staticmethod
    def record(request, event, email="", user=None, success=False):
        try:
            return AuthLog.objects.create(
                user=user,
                email=email or getattr(user, "email", ""),
                event=event,
                ip_address=get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
                success=success,
            )
        except Exception:
            logger.exception("Failed to create auth log event=%s email=%s", event, email or getattr(user, "email", ""))
            return None


class PasswordResetService:
    @staticmethod
    def request_reset(email):
        try:
            SupabaseAuthClient().request_password_reset(email=email)
        except Exception:
            logger.exception("Failed to request Supabase password reset for email=%s", email)
        # Keep the API response generic to avoid enumeration.
