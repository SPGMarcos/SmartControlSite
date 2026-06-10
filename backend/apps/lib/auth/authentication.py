import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

from apps.repositories.profiles import ProfileRepository


class SupabaseJWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode("utf-8")
        if not header:
            return None

        parts = header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        token = parts[1]
        payload = self._decode(token)
        user = self._sync_user(payload)
        return (user, token)

    def _decode(self, token):
        if not settings.SUPABASE_JWT_SECRET:
            raise exceptions.AuthenticationFailed("Supabase JWT secret nao configurado.")

        try:
            return jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                audience=settings.SUPABASE_JWT_AUDIENCE,
                options={"require": ["exp", "sub"]},
            )
        except jwt.PyJWTError as exc:
            raise exceptions.AuthenticationFailed("Token Supabase invalido ou expirado.") from exc

    def _sync_user(self, payload):
        supabase_user_id = payload.get("sub")
        email = (payload.get("email") or "").lower().strip()
        if not supabase_user_id or not email:
            raise exceptions.AuthenticationFailed("Token Supabase sem usuario valido.")

        profile = ProfileRepository.get_by_supabase_user_id(supabase_user_id)
        metadata = payload.get("user_metadata") or {}
        first_name = metadata.get("first_name") or metadata.get("name") or ""
        last_name = metadata.get("last_name") or ""

        User = get_user_model()
        user = User.objects.filter(supabase_user_id=supabase_user_id).first() or User.objects.filter(email__iexact=email).first()
        created = user is None
        if created:
            user = User(email=email, is_active=True)
        role = "admin" if (profile and profile.plano == "admin") or user.role == "admin" else "client"
        updates = []
        for field, value in {
            "supabase_user_id": supabase_user_id,
            "email": email,
            "first_name": first_name or user.first_name,
            "last_name": last_name or user.last_name,
            "role": role,
        }.items():
            if getattr(user, field) != value:
                setattr(user, field, value)
                updates.append(field)
        if created:
            user.set_unusable_password()
            updates.append("password")
        if updates:
            if created:
                user.save()
            else:
                user.save(update_fields=list(set(updates + ["updated_at"])))
        return user
