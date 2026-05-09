import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Client",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("company_name", models.CharField(max_length=180)),
                ("document", models.CharField(blank=True, max_length=32)),
                ("phone", models.CharField(blank=True, max_length=32)),
                ("status", models.CharField(choices=[("active", "Active"), ("inactive", "Inactive"), ("blocked", "Blocked")], default="active", max_length=24)),
                ("stripe_customer_id", models.CharField(blank=True, max_length=128, null=True, unique=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="client", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "clients",
                "ordering": ["company_name"],
                "indexes": [
                    models.Index(fields=["status"], name="clients_status_idx"),
                    models.Index(fields=["company_name"], name="clients_company_idx"),
                ],
            },
        ),
    ]
