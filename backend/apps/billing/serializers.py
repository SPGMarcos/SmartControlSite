from rest_framework import serializers

from apps.core.validators import sanitize_text

from .models import Payment, Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = (
            "id",
            "name",
            "slug",
            "description",
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


class SubscriptionSerializer(serializers.ModelSerializer):
    client_company = serializers.CharField(source="client.company_name", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "client",
            "client_company",
            "plan",
            "plan_name",
            "status",
            "current_period_start",
            "current_period_end",
            "cancel_at_period_end",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "client_company", "plan_name", "created_at", "updated_at")


class PaymentSerializer(serializers.ModelSerializer):
    client_company = serializers.CharField(source="client.company_name", read_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "client",
            "client_company",
            "subscription",
            "project",
            "project_name",
            "kind",
            "status",
            "amount",
            "currency",
            "paid_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CheckoutSessionSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    kind = serializers.ChoiceField(choices=Payment.Kind.choices)
    project_id = serializers.IntegerField(required=False)
