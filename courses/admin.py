from django.contrib import admin
from django.db.models import Q

from core.admin_roles import user_can_access_staff_admin, user_is_instructor, user_is_platform_admin

from .forms import ContentAdminForm
from .models import (
    Content,
    Course,
    Enrollment,
    Grade,
    Lesson,
    Message,
    Module,
    NewsletterSubscriber,
    Notification,
)


class _CoursesStaffAdminMixin:
    """Students (non-staff) never see the courses app in admin."""

    def has_module_permission(self, request):
        return user_can_access_staff_admin(request.user)


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


class ContentInline(admin.TabularInline):
    model = Content
    form = ContentAdminForm
    extra = 0


@admin.register(Course)
class CourseAdmin(_CoursesStaffAdminMixin, admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "category",
        "price",
        "instructor",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "category")
    search_fields = ("title", "slug", "description", "category")
    list_select_related = ("instructor",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = (ModuleInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if user_is_platform_admin(request.user):
            return qs
        if user_is_instructor(request.user):
            return qs.filter(instructor=request.user)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if user_is_instructor(request.user) and not user_is_platform_admin(request.user):
            obj.instructor = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if obj is None:
            return True
        if user_is_platform_admin(request.user):
            return True
        return obj.instructor_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Platform admins only (marketing list)."""

    list_display = ("email", "created_at")
    search_fields = ("email",)

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


@admin.register(Enrollment)
class EnrollmentAdmin(_CoursesStaffAdminMixin, admin.ModelAdmin):
    list_display = ("user", "course", "enrolled_at")
    list_select_related = ("user", "course")
    search_fields = ("user__username", "course__title")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if user_is_platform_admin(request.user):
            return qs
        if user_is_instructor(request.user):
            return qs.filter(course__instructor=request.user)
        return qs.none()

    def has_add_permission(self, request):
        return user_is_platform_admin(request.user)

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if user_is_platform_admin(request.user):
            return True
        if obj is None:
            return True
        return obj.course.instructor_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


@admin.register(Grade)
class GradeAdmin(_CoursesStaffAdminMixin, admin.ModelAdmin):
    list_display = ("enrollment", "score", "max_score", "updated_at")
    list_select_related = ("enrollment", "enrollment__course", "enrollment__user")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if user_is_platform_admin(request.user):
            return qs
        if user_is_instructor(request.user):
            return qs.filter(enrollment__course__instructor=request.user)
        return qs.none()

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if user_is_platform_admin(request.user):
            return True
        if obj is None:
            return True
        return obj.enrollment.course.instructor_id == request.user.id

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return user_is_platform_admin(request.user)


@admin.register(Message)
class MessageAdmin(_CoursesStaffAdminMixin, admin.ModelAdmin):
    list_display = ("id", "sender", "recipient", "course", "created_at", "read_at")
    list_select_related = ("sender", "recipient", "course")
    search_fields = ("body", "sender__username", "recipient__username")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if user_is_platform_admin(request.user):
            return qs
        if user_is_instructor(request.user):
            u = request.user
            return qs.filter(
                Q(course__instructor=u) | Q(sender=u) | Q(recipient=u)
            ).distinct()
        return qs.none()

    def has_change_permission(self, request, obj=None):
        return user_is_platform_admin(request.user)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return user_is_platform_admin(request.user)


@admin.register(Module)
class ModuleAdmin(_CoursesStaffAdminMixin, admin.ModelAdmin):
    list_display = ("title", "course", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("title", "description")
    list_select_related = ("course",)
    inlines = (LessonInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if user_is_platform_admin(request.user):
            return qs
        if user_is_instructor(request.user):
            return qs.filter(course__instructor=request.user)
        return qs.none()

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if obj is None:
            return True
        if user_is_platform_admin(request.user):
            return True
        return obj.course.instructor_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


@admin.register(Lesson)
class LessonAdmin(_CoursesStaffAdminMixin, admin.ModelAdmin):
    list_display = ("title", "module", "content_type", "created_at", "updated_at")
    list_filter = ("content_type", "created_at")
    search_fields = ("title",)
    list_select_related = ("module", "module__course")
    inlines = (ContentInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if user_is_platform_admin(request.user):
            return qs
        if user_is_instructor(request.user):
            return qs.filter(module__course__instructor=request.user)
        return qs.none()

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if obj is None:
            return True
        if user_is_platform_admin(request.user):
            return True
        return obj.module.course.instructor_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


@admin.register(Content)
class ContentAdmin(_CoursesStaffAdminMixin, admin.ModelAdmin):
    form = ContentAdminForm
    list_display = ("title", "lesson", "content_type", "order", "created_at", "updated_at")
    list_filter = ("content_type", "created_at")
    search_fields = ("title", "content")
    list_select_related = ("lesson", "lesson__module")
    ordering = ("lesson", "order")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if user_is_platform_admin(request.user):
            return qs
        if user_is_instructor(request.user):
            return qs.filter(lesson__module__course__instructor=request.user)
        return qs.none()

    def has_add_permission(self, request):
        return self.has_module_permission(request)

    def has_change_permission(self, request, obj=None):
        if not self.has_module_permission(request):
            return False
        if obj is None:
            return True
        if user_is_platform_admin(request.user):
            return True
        return obj.lesson.module.course.instructor_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Platform admins only — support / debugging."""

    list_display = ("id", "user", "kind", "title", "read_at", "created_at")
    list_filter = ("kind", "read_at", "created_at")
    search_fields = ("title", "body", "user__username")
    ordering = ("-created_at",)
    raw_id_fields = ("user",)

    def has_module_permission(self, request):
        return user_is_platform_admin(request.user)

    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_module_permission(request)
