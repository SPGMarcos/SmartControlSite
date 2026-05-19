from django.conf import settings
from django.db import models
from django.utils.text import get_valid_filename
from uuid import uuid4

from apps.clients.models import Client
from apps.core.models import TimeStampedModel


def project_attachment_upload_to(instance, filename):
    safe_name = get_valid_filename(filename.rsplit("/", 1)[-1])
    return f"projects/{instance.project_id}/attachments/{uuid4().hex}_{safe_name}"


class Project(TimeStampedModel):
    class SiteType(models.TextChoices):
        LANDING_PAGE = "landing_page", "Landing page"
        INSTITUTIONAL_SITE = "institutional_site", "Site institucional"
        WEB_SYSTEM = "web_system", "Sistema web"

    class Status(models.TextChoices):
        AWAITING_ANALYSIS = "awaiting_analysis", "Aguardando analise"
        QUOTE_SENT = "quote_sent", "Orcamento enviado"
        PAYMENT_PENDING = "payment_pending", "Pagamento pendente"
        IN_DEVELOPMENT = "in_development", "Em desenvolvimento"
        REVIEW = "review", "Revisao"
        COMPLETED = "completed", "Concluido"

    client = models.ForeignKey(Client, related_name="projects", on_delete=models.CASCADE)
    plan = models.ForeignKey("billing.Plan", related_name="projects", null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=160)
    site_type = models.CharField(max_length=32, choices=SiteType.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.AWAITING_ANALYSIS)
    domain = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    references = models.TextField(blank=True)
    desired_features = models.TextField(blank=True)
    visual_style = models.TextField(blank=True)
    repository_url = models.URLField(max_length=500, blank=True)
    production_url = models.URLField(max_length=500, blank=True)
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "projects"
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["status"]),
            models.Index(fields=["site_type"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ProjectAttachment(TimeStampedModel):
    project = models.ForeignKey(Project, related_name="attachments", on_delete=models.CASCADE)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="project_attachments", on_delete=models.RESTRICT)
    file = models.FileField(upload_to=project_attachment_upload_to)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120, blank=True)
    size = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "project_attachments"
        indexes = [
            models.Index(fields=["project"]),
            models.Index(fields=["uploaded_by"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name


class ServiceRequest(TimeStampedModel):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        WAITING_CLIENT = "waiting_client", "Waiting client"
        DONE = "done", "Done"
        CANCELED = "canceled", "Canceled"

    project = models.ForeignKey(Project, related_name="requests", on_delete=models.CASCADE)
    client = models.ForeignKey(Client, related_name="requests", on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="service_requests", on_delete=models.RESTRICT)
    title = models.CharField(max_length=180)
    description = models.TextField()
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.OPEN)

    class Meta:
        db_table = "requests"
        indexes = [
            models.Index(fields=["project"]),
            models.Index(fields=["client"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
