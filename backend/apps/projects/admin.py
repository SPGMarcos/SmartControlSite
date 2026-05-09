from django.contrib import admin

from .models import Project, ServiceRequest


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "site_type", "status", "due_date", "created_at")
    list_filter = ("site_type", "status", "created_at")
    search_fields = ("name", "client__company_name", "domain", "production_url")


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "project", "priority", "status", "created_at")
    list_filter = ("priority", "status", "created_at")
    search_fields = ("title", "description", "client__company_name", "project__name")
