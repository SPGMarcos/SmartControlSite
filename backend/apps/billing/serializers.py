from rest_framework import serializers

from apps.core.validators import sanitize_text

from .models import Payment, Plan, Subscription, TransactionLog


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "monthly_title",
            "setup_price",
            "monthly_price",
            "features",
            "is_active",
            "stripe_setup_price_id",
            "stripe_monthly_price_id",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
        extra_kwargs = {
            "stripe_setup_price_id": {"write_only": True},
            "stripe_monthly_price_id": {"write_only": True},
        }

    def validate_name(self, value):
        return sanitize_text(value)

    def validate_description(self, value):
        return sanitize_text(value)

    def validate_monthly_title(self, value):
        return sanitize_text(value)


class SubscriptionSerializer(serializers.ModelSerializer):
    client_company = serializers.CharField(source="client.company_name", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "client",
            "user",
            "client_company",
            "plan",
            "plan_name",
            "project",
            "project_name",
            "status",
            "plano",
            "stripe_customer_id",
            "stripe_subscription_id",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user", "client_company", "plan_name", "stripe_customer_id", "stripe_subscription_id", "created_at", "updated_at")


class PaymentSerializer(serializers.ModelSerializer):
    client_company = serializers.CharField(source="client.company_name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "client",
            "user",
            "client_company",
            "subscription",
            "project",
            "project_name",
            "kind",
            "status",
            "amount",
            "currency",
            "stripe_checkout_session_id",
            "stripe_payment_intent",
            "stripe_payment_intent_id",
            "stripe_invoice_id",
            "paid_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CheckoutSessionSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(required=False)
    kind = serializers.ChoiceField(choices=Payment.Kind.choices)
    project_id = serializers.IntegerField(required=False)
    installments = serializers.IntegerField(required=False, min_value=2, max_value=12)

    def validate(self, attrs):
        if "plan_id" not in attrs and "project_id" not in attrs:
            raise serializers.ValidationError("Informe um plano ou projeto para pagamento.")
        if attrs.get("kind") == Payment.Kind.SUBSCRIPTION and attrs.get("installments"):
            raise serializers.ValidationError("Parcelamento se aplica apenas a pagamentos de projeto.")
        return attrs


class TransactionLogSerializer(serializers.ModelSerializer):
    client_company = serializers.CharField(source="client.company_name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = TransactionLog
        fields = (
            "id",
            "provider",
            "stripe_event_id",
            "event_type",
            "status",
            "client",
            "client_company",
            "subscription",
            "project",
            "project_name",
            "payment",
            "amount",
            "currency",
            "payload",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
