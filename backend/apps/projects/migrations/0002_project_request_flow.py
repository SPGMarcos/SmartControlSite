import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import apps.projects.models


def normalize_project_values(apps, schema_editor):
    Project = apps.get_model("projects", "Project")
    site_types = {
        "online_store": "institutional_site",
        "system": "web_system",
    }
    statuses = {
        "planning": "awaiting_analysis",
        "design": "quote_sent",
        "development": "in_development",
        "review": "review",
        "published": "completed",
        "paused": "awaiting_analysis",
        "canceled": "awaiting_analysis",
    }

    for project in Project.objects.all().only("id", "site_type", "status"):
        changed = False
        if project.site_type in site_types:
            project.site_type = site_types[project.site_type]
            changed = True
        if project.status in statuses:
            project.status = statuses[project.status]
            changed = True
        if changed:
            project.save(update_fields=["site_type", "status"])


class Migration(migrations.Migration):
    dependencies = [
        ("projects", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="desired_features",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="project",
            name="references",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="project",
            name="visual_style",
            field=models.TextField(blank=True, default=""),
            preserve_default=False,
        ),
        migrations.RunPython(normalize_project_values, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="project",
            name="site_type",
            field=models.CharField(
                choices=[
                    ("landing_page", "Landing page"),
                    ("institutional_site", "Site institucional"),
                    ("web_system", "Sistema web"),
                ],
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="status",
            field=models.CharField(
                choices=[
                    ("awaiting_analysis", "Aguardando analise"),
                    ("quote_sent", "Orcamento enviado"),
                    ("payment_pending", "Pagamento pendente"),
                    ("in_development", "Em desenvolvimento"),
                    ("review", "Revisao"),
                    ("completed", "Concluido"),
                ],
                default="awaiting_analysis",
                max_length=32,
            ),
        ),
        migrations.CreateModel(
            name="ProjectAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("file", models.FileField(upload_to=apps.projects.models.project_attachment_upload_to)),
                ("original_name", models.CharField(max_length=255)),
                ("content_type", models.CharField(blank=True, max_length=120)),
                ("size", models.PositiveIntegerField(default=0)),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attachments",
                        to="projects.project",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="project_attachments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "project_attachments",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(fields=["project"], name="project_att_project_idx"),
                    models.Index(fields=["uploaded_by"], name="project_att_user_idx"),
                ],
            },
        ),
    ]
