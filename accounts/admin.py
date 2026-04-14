from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Profile

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'role', 'is_active', 'is_staff', 'first_name', 'last_name', 'profile')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    model = Profile
    list_display = ('user', 'bio', 'avatar')
