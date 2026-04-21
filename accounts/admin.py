from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from core.admin_roles import user_is_platform_admin

from .models import CustomUser, Profile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        "email",
        "role",
        "is_active",
        "is_staff",
        "first_name",
        "last_name",
        "profile",
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("Custom fields", {"fields": ("role",)}),
    )

    def has_module_permission(self, request):
        return user_is_platform_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    model = Profile
    list_display = ("user", "bio", "avatar")

    def has_module_permission(self, request):
        return request.user.is_authenticated and request.user.is_staff

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if user_is_platform_admin(request.user):
            return qs
        return qs.filter(user=request.user)

    def has_change_permission(self, request, obj=None):
        if not request.user.is_authenticated or not request.user.is_staff:
            return False
        if user_is_platform_admin(request.user):
            return True
        if obj is None:
            return True
        return obj.user_id == request.user.id

    def has_view_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return user_is_platform_admin(request.user)
