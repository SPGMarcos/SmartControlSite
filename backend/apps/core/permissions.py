from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.role == "admin")


class IsAdminOrClientOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        client = getattr(obj, "client", None)
        if client and client.user_id == request.user.id:
            return True
        if getattr(obj, "user_id", None) == request.user.id:
            return True
        return False
