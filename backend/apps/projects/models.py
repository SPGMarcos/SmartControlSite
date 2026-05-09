from django.conf import settings
from django.db import models

from apps.clients.models import Client
from apps.core.models import TimeStampedModel


class Project(TimeStampedModel):
    class SiteType(models.TextChoices):
        LANDING_PAGE = "landing_page", "Landing page"
        ONLINE_STORE = "online_store", "Online store"
        SYSTEM = "system", "System"

    class Status(models.TextChoices):
        PLANNING = "planning", "Planning"
        DESIGN = "design", "Design"
        DEVELOPMENT = "development", "Development"
        REVIEW = "review", "Review"
        PUBLISHED = "published", "Published"
        PAUSED = "paused", "Paused"
        CANCELED = "canceled", "Canceled"

    client = models.ForeignKey(Client, related_name="projects", on_delete=models.CASCADE)
    plan = models.ForeignKey("billing.Plan", related_name="projects", null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=160)
    site_type = models.CharField(max_length=32, choices=SiteType.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PLANNING)
    domain = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
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
