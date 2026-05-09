import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0001_initial"),
        ("clients", "0001_initial"),
        ("projects", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("kind", models.CharField(choices=[("one_time", "One time"), ("subscription", "Subscription")], max_length=24)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed"), ("refunded", "Refunded"), ("canceled", "Canceled")], default="pending", max_length=24)),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(default="BRL", max_length=3)),
                ("stripe_payment_intent_id", models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ("stripe_invoice_id", models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="clients.client")),
                ("project", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments", to="projects.project")),
                ("subscription", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments", to="billing.subscription")),
            ],
            options={
                "db_table": "payments",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["client"], name="billing_pay_client_idx"),
                    models.Index(fields=["status"], name="billing_pay_status_idx"),
                    models.Index(fields=["kind"], name="billing_pay_kind_idx"),
                ],
            },
        ),
    ]
