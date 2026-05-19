import os

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.clients.models import Client
from apps.users.models import User


def first_env(*names, default=""):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value.strip()
    return default


class Command(BaseCommand):
    help = "Creates or updates login users from Render/Django environment credentials."

    def handle(self, *args, **options):
        created_any = False
        created_any |= self.bootstrap_admin()
        created_any |= self.bootstrap_client()
        if not created_any:
            self.stdout.write("No bootstrap login credentials configured.")

    @transaction.atomic
    def bootstrap_admin(self):
        email = first_env(
            "SMARTCONTROL_ADMIN_EMAIL",
            "ADMIN_EMAIL",
            "DJANGO_ADMIN_EMAIL",
            "DJANGO_SUPERUSER_EMAIL",
            "SUPERUSER_EMAIL",
            "RENDER_ADMIN_EMAIL",
        )
        password = first_env(
            "SMARTCONTROL_ADMIN_PASSWORD",
            "ADMIN_PASSWORD",
            "DJANGO_ADMIN_PASSWORD",
            "DJANGO_SUPERUSER_PASSWORD",
            "SUPERUSER_PASSWORD",
            "RENDER_ADMIN_PASSWORD",
        )
        first_name = first_env("SMARTCONTROL_ADMIN_FIRST_NAME", "ADMIN_FIRST_NAME", "DJANGO_SUPERUSER_FIRST_NAME", default="Admin")
        last_name = first_env("SMARTCONTROL_ADMIN_LAST_NAME", "ADMIN_LAST_NAME", "DJANGO_SUPERUSER_LAST_NAME", default="SmartControl")

        if not email or not password:
            return False

        user, created = User.objects.get_or_create(
            email=email.lower(),
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        user.role = User.Role.ADMIN
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} admin login for {user.email}."))
        return True

    @transaction.atomic
    def bootstrap_client(self):
        email = first_env("SMARTCONTROL_CLIENT_EMAIL", "CLIENT_EMAIL")
        password = first_env("SMARTCONTROL_CLIENT_PASSWORD", "CLIENT_PASSWORD")
        first_name = first_env("SMARTCONTROL_CLIENT_FIRST_NAME", "CLIENT_FIRST_NAME", default="Cliente")
        last_name = first_env("SMARTCONTROL_CLIENT_LAST_NAME", "CLIENT_LAST_NAME", default="")
        company_name = first_env("SMARTCONTROL_CLIENT_COMPANY", "CLIENT_COMPANY", default="SmartControl Cliente")
        phone = first_env("SMARTCONTROL_CLIENT_PHONE", "CLIENT_PHONE", default="")

        if not email or not password:
            return False

        user, created = User.objects.get_or_create(
            email=email.lower(),
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "role": User.Role.CLIENT,
                "is_active": True,
            },
        )
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        user.role = User.Role.CLIENT
        user.is_active = True
        user.set_password(password)
        user.save()

        Client.objects.update_or_create(
            user=user,
            defaults={
                "company_name": company_name,
                "phone": phone,
            },
        )

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} client login for {user.email}."))
        return True
