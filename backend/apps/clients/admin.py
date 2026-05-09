from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("company_name", "user", "status", "phone", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("company_name", "user__email", "document", "phone", "stripe_customer_id")
