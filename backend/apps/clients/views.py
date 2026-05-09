from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.core.permissions import IsAdmin, IsAdminOrClientOwner
from apps.core.services import audit

from .models import Client
from .serializers import ClientCreateSerializer, ClientSerializer


class ClientViewSet(ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, IsAdminOrClientOwner]
    search_fields = ("company_name", "user__email", "document")
    ordering_fields = ("company_name", "created_at", "status")

    def get_queryset(self):
        queryset = Client.objects.select_related("user")
        if self.request.user.role == "admin":
            return queryset
        return queryset.filter(user=self.request.user)

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdmin()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "create":
            return ClientCreateSerializer
        return ClientSerializer

    def perform_create(self, serializer):
        client = serializer.save()
        audit(self.request.user, "client.create", request=self.request, target=client)

    def perform_update(self, serializer):
        client = serializer.save()
        audit(self.request.user, "client.update", request=self.request, target=client)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        client = Client.objects.select_related("user").get(user=request.user)
        return Response(ClientSerializer(client).data)
