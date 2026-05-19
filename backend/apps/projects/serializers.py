from pathlib import Path

from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from apps.billing.models import Plan
from apps.clients.models import Client
from apps.core.validators import sanitize_text

from .models import Project, ProjectAttachment, ServiceRequest


class ProjectAttachmentSerializer(serializers.ModelSerializer):
    url = serializers.FileField(source="file", read_only=True)

    class Meta:
        model = ProjectAttachment
        fields = (
            "id",
            "original_name",
            "content_type",
            "size",
            "url",
            "created_at",
        )
        read_only_fields = fields


class ProjectSerializer(serializers.ModelSerializer):
    client_id = serializers.PrimaryKeyRelatedField(source="client", queryset=Client.objects.all(), required=False)
    plan_id = serializers.PrimaryKeyRelatedField(source="plan", queryset=Plan.objects.all(), required=False, allow_null=True)
    client_company = serializers.CharField(source="client.company_name", read_only=True)
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    attachments = ProjectAttachmentSerializer(many=True, read_only=True)
    uploaded_files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True,
        allow_empty=True,
    )

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
            "references",
            "desired_features",
            "visual_style",
            "attachments",
            "uploaded_files",
            "repository_url",
            "production_url",
            "start_date",
            "due_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "client_company", "plan_name", "created_at", "updated_at")

    def validate(self, attrs):
        request = self.context["request"]
        is_admin = request.user.role == "admin"

        if not is_admin:
            try:
                client = request.user.client
            except Client.DoesNotExist:
                raise serializers.ValidationError("Perfil de cliente nao encontrado.")
            if self.instance and "status" in attrs:
                raise serializers.ValidationError("Status so pode ser alterado pelo administrador.")
            attrs["client"] = client
            attrs["status"] = Project.Status.AWAITING_ANALYSIS
            attrs.pop("plan", None)
        elif self.instance is None and "client" not in attrs:
            raise serializers.ValidationError({"client_id": "Informe o cliente do projeto."})

        return attrs

    def validate_name(self, value):
        return sanitize_text(value)

    def validate_domain(self, value):
        return sanitize_text(value)

    def validate_description(self, value):
        return sanitize_text(value)

    def validate_references(self, value):
        return sanitize_text(value)

    def validate_desired_features(self, value):
        return sanitize_text(value)

    def validate_visual_style(self, value):
        return sanitize_text(value)

    def validate_uploaded_files(self, files):
        max_files = getattr(settings, "PROJECT_ATTACHMENT_MAX_FILES", 10)
        max_size = getattr(settings, "PROJECT_ATTACHMENT_MAX_SIZE", 10 * 1024 * 1024)
        allowed_extensions = getattr(settings, "PROJECT_ATTACHMENT_ALLOWED_EXTENSIONS", set())
        allowed_content_types = getattr(settings, "PROJECT_ATTACHMENT_ALLOWED_CONTENT_TYPES", set())

        if len(files) > max_files:
            raise serializers.ValidationError(f"Envie no maximo {max_files} arquivos.")

        for item in files:
            extension = Path(item.name).suffix.lower()
            content_type = getattr(item, "content_type", "")
            if item.size > max_size:
                raise serializers.ValidationError(f"O arquivo {item.name} excede o limite permitido.")
            if allowed_extensions and extension not in allowed_extensions:
                raise serializers.ValidationError(f"O arquivo {item.name} possui extensao nao permitida.")
            if allowed_content_types and content_type and content_type not in allowed_content_types:
                raise serializers.ValidationError(f"O arquivo {item.name} possui tipo nao permitido.")
        return files

    @transaction.atomic
    def create(self, validated_data):
        uploaded_files = validated_data.pop("uploaded_files", [])
        project = Project.objects.create(**validated_data)
        self._create_attachments(project, uploaded_files)
        return project

    @transaction.atomic
    def update(self, instance, validated_data):
        uploaded_files = validated_data.pop("uploaded_files", [])
        project = super().update(instance, validated_data)
        self._create_attachments(project, uploaded_files)
        return project

    def _create_attachments(self, project, uploaded_files):
        user = self.context["request"].user
        for item in uploaded_files:
            ProjectAttachment.objects.create(
                project=project,
                uploaded_by=user,
                file=item,
                original_name=sanitize_text(item.name),
                content_type=getattr(item, "content_type", ""),
                size=item.size,
            )


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
