import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Plan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=120)),
                ("slug", models.SlugField(max_length=140, unique=True)),
                ("description", models.TextField(blank=True)),
                ("setup_price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("monthly_price", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("features", models.JSONField(blank=True, default=list)),
                ("is_active", models.BooleanField(default=True)),
                ("stripe_setup_price_id", models.CharField(blank=True, max_length=128)),
                ("stripe_monthly_price_id", models.CharField(blank=True, max_length=128)),
            ],
            options={
                "db_table": "plans",
                "ordering": ["setup_price", "monthly_price"],
                "indexes": [models.Index(fields=["is_active"], name="billing_plan_active_idx")],
            },
        ),
        migrations.CreateModel(
            name="Subscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("active", "Active"), ("past_due", "Past due"), ("canceled", "Canceled"), ("unpaid", "Unpaid"), ("incomplete", "Incomplete")], default="pending", max_length=32)),
                ("stripe_subscription_id", models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ("current_period_start", models.DateTimeField(blank=True, null=True)),
                ("current_period_end", models.DateTimeField(blank=True, null=True)),
                ("cancel_at_period_end", models.BooleanField(default=False)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subscriptions", to="clients.client")),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name="subscriptions", to="billing.plan")),
            ],
            options={
                "db_table": "subscriptions",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["client"], name="billing_sub_client_idx"),
                    models.Index(fields=["status"], name="billing_sub_status_idx"),
                ],
            },
        ),
    ]
