import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("billing", "0001_initial"),
        ("clients", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Project",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=160)),
                ("site_type", models.CharField(choices=[("landing_page", "Landing page"), ("online_store", "Online store"), ("system", "System")], max_length=32)),
                ("status", models.CharField(choices=[("planning", "Planning"), ("design", "Design"), ("development", "Development"), ("review", "Review"), ("published", "Published"), ("paused", "Paused"), ("canceled", "Canceled")], default="planning", max_length=32)),
                ("domain", models.CharField(blank=True, max_length=255)),
                ("description", models.TextField(blank=True)),
                ("repository_url", models.URLField(blank=True, max_length=500)),
                ("production_url", models.URLField(blank=True, max_length=500)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="projects", to="clients.client")),
                ("plan", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="projects", to="billing.plan")),
            ],
            options={
                "db_table": "projects",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["client"], name="projects_client_idx"),
                    models.Index(fields=["status"], name="projects_status_idx"),
                    models.Index(fields=["site_type"], name="projects_site_type_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="ServiceRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=180)),
                ("description", models.TextField()),
                ("priority", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")], default="medium", max_length=16)),
                ("status", models.CharField(choices=[("open", "Open"), ("in_progress", "In progress"), ("waiting_client", "Waiting client"), ("done", "Done"), ("canceled", "Canceled")], default="open", max_length=24)),
                ("client", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="requests", to="clients.client")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name="service_requests", to=settings.AUTH_USER_MODEL)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="requests", to="projects.project")),
            ],
            options={
                "db_table": "requests",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["project"], name="requests_project_idx"),
                    models.Index(fields=["client"], name="requests_client_idx"),
                    models.Index(fields=["status"], name="requests_status_idx"),
                ],
            },
        ),
    ]
