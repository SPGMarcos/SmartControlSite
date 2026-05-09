from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers

from apps.core.validators import sanitize_text
from apps.clients.models import Client

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
            raise serializers.ValidationError("Nao foi possivel concluir o cadastro.")
        return email

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=sanitize_text(validated_data["first_name"]),
            last_name=sanitize_text(validated_data.get("last_name", "")),
            role=User.Role.CLIENT,
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
        request = self.context.get("request")
        email = attrs["email"].lower().strip()
        user = authenticate(request=request, username=email, password=attrs["password"])
        if not user or not user.is_active:
            raise serializers.ValidationError("Credenciais invalidas.")
        attrs["user"] = user
        attrs["email"] = email
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=10)

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Token invalido ou expirado.")

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("Token invalido ou expirado.")
        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)
