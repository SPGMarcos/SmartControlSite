from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_rename_users_auth_email_idx_auth_logs_email_a5e514_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="supabase_user_id",
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("nome", models.CharField(max_length=180)),
                ("plano", models.CharField(default="client", max_length=40)),
                ("creditos", models.PositiveIntegerField(default=0)),
            ],
            options={
                "db_table": "profiles",
                "ordering": ["nome"],
            },
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["supabase_user_id"], name="users_supabase_70929c_idx"),
        ),
        migrations.AddIndex(
            model_name="profile",
            index=models.Index(fields=["email"], name="profiles_email_973221_idx"),
        ),
        migrations.AddIndex(
            model_name="profile",
            index=models.Index(fields=["plano"], name="profiles_plano_97a85c_idx"),
        ),
    ]
