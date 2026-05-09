from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.core.permissions import IsAdmin, IsAdminOrClientOwner
from apps.core.services import audit

from .models import Project, ServiceRequest
from .serializers import ProjectSerializer, ServiceRequestSerializer


class ProjectViewSet(ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsAdminOrClientOwner]
    filterset_fields = ("status", "site_type", "client")
    search_fields = ("name", "domain", "client__company_name")
    ordering_fields = ("created_at", "due_date", "status", "name")

    def get_queryset(self):
        queryset = Project.objects.select_related("client", "plan", "client__user")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(client__user=self.request.user)

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdmin()]
        return super().get_permissions()

    def perform_create(self, serializer):
        project = serializer.save()
        audit(self.request.user, "project.create", request=self.request, target=project)

    def perform_update(self, serializer):
        project = serializer.save()
        audit(self.request.user, "project.update", request=self.request, target=project)


class ServiceRequestViewSet(ModelViewSet):
    serializer_class = ServiceRequestSerializer
    permission_classes = [IsAuthenticated, IsAdminOrClientOwner]
    filterset_fields = ("status", "priority", "project")
    search_fields = ("title", "description", "project__name", "client__company_name")
    ordering_fields = ("created_at", "priority", "status")

    def get_queryset(self):
        queryset = ServiceRequest.objects.select_related("project", "client", "created_by", "client__user")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(client__user=self.request.user)

    def perform_create(self, serializer):
        item = serializer.save()
        audit(self.request.user, "request.create", request=self.request, target=item)

    def perform_update(self, serializer):
        item = serializer.save()
        audit(self.request.user, "request.update", request=self.request, target=item)
