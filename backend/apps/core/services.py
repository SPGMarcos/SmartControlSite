from .models import AuditLog


def get_client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def audit(actor, action, request=None, target=None, metadata=None):
    target_type = target.__class__.__name__ if target is not None else ""
    target_id = str(getattr(target, "pk", "")) if target is not None else ""
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        target_type=target_type,
        target_id=target_id,
        ip_address=get_client_ip(request) if request else None,
        metadata=metadata or {},
    )
