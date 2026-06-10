from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from apps.core.validators import sanitize_text
from apps.clients.models import Client
from apps.lib.supabase.client import SupabaseAuthClient
from apps.repositories.profiles import ProfileRepository

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "role", "is_active", "created_at")
        read_only_fields = fields


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    company_name = serializers.CharField(max_length=180)
    document = serializers.CharField(max_length=32, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Este email ja esta cadastrado. Acesse com login ou recupere sua senha.")
        return email

    @transaction.atomic
    def create(self, validated_data):
        first_name = sanitize_text(validated_data["first_name"])
        last_name = sanitize_text(validated_data.get("last_name", ""))
        full_name = " ".join(item for item in [first_name, last_name] if item).strip()
        supabase_user = SupabaseAuthClient().create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            metadata={
                "first_name": first_name,
                "last_name": last_name,
                "company_name": sanitize_text(validated_data["company_name"]),
            },
        )
        supabase_user_id = supabase_user["id"]
        user = User.objects.create_user(
            email=validated_data["email"],
            password=None,
            first_name=sanitize_text(validated_data["first_name"]),
            last_name=sanitize_text(validated_data.get("last_name", "")),
            supabase_user_id=supabase_user_id,
            role=User.Role.CLIENT,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        ProfileRepository.upsert_from_registration(
            supabase_user_id=supabase_user_id,
            email=user.email,
            nome=full_name or user.email,
        )
        Client.objects.create(
            user=user,
            company_name=sanitize_text(validated_data["company_name"]),
            document=sanitize_text(validated_data.get("document", "")),
            phone=sanitize_text(validated_data.get("phone", "")),
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs["email"].lower().strip()
        session = SupabaseAuthClient().sign_in_with_password(email=email, password=attrs["password"])
        supabase_user = session.get("user") or {}
        supabase_user_id = supabase_user.get("id")
        user = User.objects.filter(supabase_user_id=supabase_user_id).first() or User.objects.filter(email__iexact=email).first()
        if not user:
            metadata = supabase_user.get("user_metadata") or {}
            user = User.objects.create_user(
                email=email,
                password=None,
                first_name=sanitize_text(metadata.get("first_name") or metadata.get("name") or ""),
                last_name=sanitize_text(metadata.get("last_name") or ""),
                supabase_user_id=supabase_user_id,
                role=User.Role.CLIENT,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])
            ProfileRepository.upsert_from_registration(
                supabase_user_id=supabase_user_id,
                email=email,
                nome=" ".join(item for item in [user.first_name, user.last_name] if item).strip() or email,
            )
        if not user.is_active:
            raise serializers.ValidationError("Credenciais invalidas.")
        if supabase_user_id and user.supabase_user_id != supabase_user_id:
            user.supabase_user_id = supabase_user_id
            user.save(update_fields=["supabase_user_id", "updated_at"])
        attrs["user"] = user
        attrs["email"] = email
        attrs["session"] = session
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=10)

    def validate_new_password(self, value):
        validate_password(value)
        return value


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)
    access = serializers.CharField(required=False, allow_blank=True)
