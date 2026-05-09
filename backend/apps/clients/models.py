from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Client(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"
        BLOCKED = "blocked", "Blocked"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="client", on_delete=models.CASCADE)
    company_name = models.CharField(max_length=180)
    document = models.CharField(max_length=32, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ACTIVE)
    stripe_customer_id = models.CharField(max_length=128, unique=True, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["company_name"]),
        ]
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name
