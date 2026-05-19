import ipaddress
import logging

from .models import AuditLog


logger = logging.getLogger(__name__)


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    raw_ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")
    if not raw_ip:
        return None
    if raw_ip.startswith("[") and "]" in raw_ip:
        raw_ip = raw_ip[1 : raw_ip.index("]")]
    elif raw_ip.count(":") == 1 and "." in raw_ip:
        raw_ip = raw_ip.split(":", 1)[0]
    try:
        return str(ipaddress.ip_address(raw_ip))
    except ValueError:
        logger.warning("Invalid client IP ignored: %s", raw_ip)
        return None


def audit(actor, action, request=None, target=None, metadata=None):
    target_type = target.__class__.__name__ if target is not None else ""
    target_id = str(getattr(target, "pk", "")) if target is not None else ""
    try:
        return AuditLog.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            ip_address=get_client_ip(request) if request else None,
            metadata=metadata or {},
        )
    except Exception:
        logger.exception("Failed to create audit log action=%s target=%s:%s", action, target_type, target_id)
        return None
