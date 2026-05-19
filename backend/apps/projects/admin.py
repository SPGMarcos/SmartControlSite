from django.contrib import admin

from .models import Project, ProjectAttachment, ServiceRequest


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "client", "site_type", "status", "plan", "due_date", "created_at")
    list_filter = ("site_type", "status", "created_at")
    search_fields = ("name", "client__company_name", "domain", "production_url", "references", "desired_features")


@admin.register(ProjectAttachment)
class ProjectAttachmentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "project", "uploaded_by", "content_type", "size", "created_at")
    list_filter = ("content_type", "created_at")
    search_fields = ("original_name", "project__name", "uploaded_by__email")


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ("title", "client", "project", "priority", "status", "created_at")
    list_filter = ("priority", "status", "created_at")
    search_fields = ("title", "description", "client__company_name", "project__name")
