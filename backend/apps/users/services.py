import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.core.services import get_client_ip

from .models import AuthLog

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthLogService:
    @staticmethod
    def record(request, event, email="", user=None, success=False):
        return AuthLog.objects.create(
            user=user,
            email=email or getattr(user, "email", ""),
            event=event,
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:1000],
            success=success,
        )


class PasswordResetService:
    @staticmethod
    def request_reset(email):
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
        logger.info("Password reset requested for user_id=%s reset_url=%s", user.pk, reset_url if settings.DEBUG else "[redacted]")
        # Hook real email delivery here. Keep the API response generic to avoid enumeration.
