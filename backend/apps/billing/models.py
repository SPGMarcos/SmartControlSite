from django.db import models

from apps.clients.models import Client
from apps.core.models import TimeStampedModel


class Plan(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    setup_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    features = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    stripe_setup_price_id = models.CharField(max_length=128, blank=True)
    stripe_monthly_price_id = models.CharField(max_length=128, blank=True)

    class Meta:
        db_table = "plans"
        indexes = [models.Index(fields=["is_active"])]
        ordering = ["setup_price", "monthly_price"]

    def __str__(self):
        return self.name


class Subscription(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        PAST_DUE = "past_due", "Past due"
        CANCELED = "canceled", "Canceled"
        UNPAID = "unpaid", "Unpaid"
        INCOMPLETE = "incomplete", "Incomplete"

    client = models.ForeignKey(Client, related_name="subscriptions", on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, related_name="subscriptions", on_delete=models.RESTRICT)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING)
    stripe_subscription_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)

    class Meta:
        db_table = "subscriptions"
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["status"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client} - {self.plan} ({self.status})"


class Payment(TimeStampedModel):
    class Kind(models.TextChoices):
        ONE_TIME = "one_time", "One time"
        SUBSCRIPTION = "subscription", "Subscription"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"
        CANCELED = "canceled", "Canceled"

    client = models.ForeignKey(Client, related_name="payments", on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, related_name="payments", null=True, blank=True, on_delete=models.SET_NULL)
    project = models.ForeignKey("projects.Project", related_name="payments", null=True, blank=True, on_delete=models.SET_NULL)
    kind = models.CharField(max_length=24, choices=Kind.choices)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="BRL")
    stripe_payment_intent_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    stripe_invoice_id = models.CharField(max_length=128, unique=True, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["client"]),
            models.Index(fields=["status"]),
            models.Index(fields=["kind"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.client} {self.kind} {self.amount} {self.status}"
