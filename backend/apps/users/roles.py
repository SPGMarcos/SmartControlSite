from django.conf import settings


def normalize_email(email):
    return str(email or "").lower().strip()


def is_primary_admin_email(email):
    return normalize_email(email) in {normalize_email(item) for item in settings.PRIMARY_ADMIN_EMAILS}


def resolved_role_for_user(email, current_role="client"):
    if is_primary_admin_email(email) or current_role == "admin":
        return "admin"
    return "client"


def apply_persistent_role(user):
    role = resolved_role_for_user(user.email, getattr(user, "role", "client"))
    user.role = role
    if role == "admin":
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
    return user
