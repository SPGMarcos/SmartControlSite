from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from apps.core.validators import sanitize_text
from apps.lib.supabase.client import SupabaseAuthClient
from apps.repositories.profiles import ProfileRepository
from apps.users.serializers import UserSerializer

from .models import Client

User = get_user_model()


class ClientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Client
        fields = (
            "id",
            "user",
            "company_name",
            "document",
            "phone",
            "status",
            "stripe_customer_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "stripe_customer_id", "created_at", "updated_at")

    def validate_company_name(self, value):
        return sanitize_text(value)

    def validate_document(self, value):
        return sanitize_text(value)

    def validate_phone(self, value):
        return sanitize_text(value)


class ClientCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    company_name = serializers.CharField(max_length=180)
    document = serializers.CharField(max_length=32, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    status = serializers.ChoiceField(choices=Client.Status.choices, default=Client.Status.ACTIVE)

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Nao foi possivel criar o cliente.")
        return email

    @transaction.atomic
    def create(self, validated_data):
        first_name = sanitize_text(validated_data["first_name"])
        last_name = sanitize_text(validated_data.get("last_name", ""))
        supabase_user = SupabaseAuthClient().create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            metadata={
                "first_name": first_name,
                "last_name": last_name,
                "company_name": sanitize_text(validated_data["company_name"]),
            },
        )
        user = User.objects.create_user(
            email=validated_data["email"],
            password=None,
            first_name=first_name,
            last_name=last_name,
            supabase_user_id=supabase_user["id"],
            role=User.Role.CLIENT,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])
        ProfileRepository.upsert_from_registration(
            supabase_user_id=supabase_user["id"],
            email=user.email,
            nome=" ".join(item for item in [first_name, last_name] if item).strip() or user.email,
        )
        return Client.objects.create(
            user=user,
            company_name=sanitize_text(validated_data["company_name"]),
            document=sanitize_text(validated_data.get("document", "")),
            phone=sanitize_text(validated_data.get("phone", "")),
            status=validated_data.get("status", Client.Status.ACTIVE),
        )
