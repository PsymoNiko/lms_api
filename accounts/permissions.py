from rest_framework.permissions import BasePermission


class IsPlatformAdmin(BasePermission):
    """JWT user with role `admin` or Django superuser."""

    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if u.is_superuser:
            return True
        return getattr(u, "role", None) == "admin"
