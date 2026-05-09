from rest_framework import serializers

from apps.billing.models import Plan
from apps.clients.models import Client
from apps.core.validators import sanitize_text

from .models import Project, ServiceRequest


class ProjectSerializer(serializers.ModelSerializer):
    client_id = serializers.PrimaryKeyRelatedField(source="client", queryset=Client.objects.all(), write_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(source="plan", queryset=Plan.objects.all(), required=False, allow_null=True, write_only=True)
    client_company = serializers.CharField(source="client.company_name", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = Project
        fields = (
            "id",
            "client_id",
            "client_company",
            "plan_id",
            "plan_name",
            "name",
            "site_type",
            "status",
            "domain",
            "description",
            "repository_url",
            "production_url",
            "start_date",
            "due_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "client_company", "plan_name", "created_at", "updated_at")

    def validate_name(self, value):
        return sanitize_text(value)

    def validate_domain(self, value):
        return sanitize_text(value)

    def validate_description(self, value):
        return sanitize_text(value)


class ServiceRequestSerializer(serializers.ModelSerializer):
    project_id = serializers.PrimaryKeyRelatedField(source="project", queryset=Project.objects.select_related("client"), write_only=True)
    project_name = serializers.CharField(source="project.name", read_only=True)
    client_company = serializers.CharField(source="client.company_name", read_only=True)
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)

    class Meta:
        model = ServiceRequest
        fields = (
            "id",
            "project_id",
            "project_name",
            "client_company",
            "created_by_email",
            "title",
            "description",
            "priority",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "project_name", "client_company", "created_by_email", "created_at", "updated_at")

    def validate(self, attrs):
        request = self.context["request"]
        project = attrs.get("project") or getattr(self.instance, "project", None)
        if request.user.role != "admin" and project.client.user_id != request.user.id:
            raise serializers.ValidationError("Projeto nao encontrado.")
        if self.instance and request.user.role != "admin" and "status" in attrs:
            raise serializers.ValidationError("Status so pode ser alterado pelo administrador.")
        return attrs

    def validate_title(self, value):
        return sanitize_text(value)

    def validate_description(self, value):
        return sanitize_text(value)

    def create(self, validated_data):
        project = validated_data["project"]
        return ServiceRequest.objects.create(
            project=project,
            client=project.client,
            created_by=self.context["request"].user,
            **{key: value for key, value in validated_data.items() if key != "project"},
        )
