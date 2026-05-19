import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0002_payment"),
        ("clients", "0001_initial"),
        ("projects", "0002_project_request_flow"),
    ]

    operations = [
        migrations.AddField(
            model_name="subscription",
            name="project",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="subscriptions",
                to="projects.project",
            ),
        ),
        migrations.AlterField(
            model_name="payment",
            name="kind",
            field=models.CharField(
                choices=[
                    ("one_time", "One time"),
                    ("subscription", "Subscription"),
                    ("installment", "Installment"),
                ],
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="payment",
            name="metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="payment",
            name="stripe_checkout_session_id",
            field=models.CharField(blank=True, max_length=128, null=True, unique=True),
        ),
        migrations.AddIndex(
            model_name="payment",
            index=models.Index(fields=["stripe_checkout_session_id"], name="billing_pay_session_idx"),
        ),
        migrations.CreateModel(
            name="TransactionLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("provider", models.CharField(default="stripe", max_length=32)),
                ("stripe_event_id", models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ("event_type", models.CharField(max_length=120)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("processed", "Processed"),
                            ("ignored", "Ignored"),
                            ("failed", "Failed"),
                            ("duplicate", "Duplicate"),
                        ],
                        default="created",
                        max_length=24,
                    ),
                ),
                ("amount", models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ("currency", models.CharField(blank=True, max_length=3)),
                ("payload", models.JSONField(blank=True, default=dict)),
                (
                    "client",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transaction_logs",
                        to="clients.client",
                    ),
                ),
                (
                    "payment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transaction_logs",
                        to="billing.payment",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transaction_logs",
                        to="projects.project",
                    ),
                ),
                (
                    "subscription",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="transaction_logs",
                        to="billing.subscription",
                    ),
                ),
            ],
            options={
                "db_table": "transaction_logs",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["provider", "event_type"], name="billing_log_provider_idx"),
                    models.Index(fields=["status"], name="billing_log_status_idx"),
                    models.Index(fields=["client"], name="billing_log_client_idx"),
                    models.Index(fields=["created_at"], name="billing_log_created_idx"),
                ],
            },
        ),
    ]
