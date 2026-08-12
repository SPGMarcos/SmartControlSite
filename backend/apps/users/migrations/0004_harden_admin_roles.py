from django.db import migrations
from django.utils import timezone


PRIMARY_ADMIN_EMAIL = "mgfm554@gmail.com"


def promote_primary_admin(apps, schema_editor):
    User = apps.get_model("users", "User")
    User.objects.filter(email__iexact=PRIMARY_ADMIN_EMAIL).update(
        role="admin",
        is_staff=True,
        is_superuser=True,
        is_active=True,
        updated_at=timezone.now(),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0003_supabase_profiles"),
    ]

    operations = [
        migrations.RunPython(promote_primary_admin, migrations.RunPython.noop),
        migrations.RunSQL(
            sql="""
            create or replace function public.handle_new_auth_user()
            returns trigger
            language plpgsql
            security definer
            set search_path = public
            as $$
            begin
              insert into public.profiles (id, email, nome, plano, creditos)
              values (
                new.id,
                new.email,
                coalesce(new.raw_user_meta_data->>'name', new.raw_user_meta_data->>'first_name', new.email),
                'client',
                0
              )
              on conflict (id) do update
                set email = excluded.email,
                    nome = excluded.nome,
                    updated_at = now();
              return new;
            end;
            $$;

            drop policy if exists "profiles_update_own" on public.profiles;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
