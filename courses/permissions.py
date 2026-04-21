from django.db.models import Q
from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.models import CustomUser


def _course_for_obj(obj):
    if hasattr(obj, "instructor_id"):
        return obj
    if hasattr(obj, "course"):
        return obj.course
    if hasattr(obj, "module"):
        return obj.module.course
    if hasattr(obj, "lesson"):
        return obj.lesson.module.course
    return None


class DenyStudentCourseWrite(BasePermission):
    """Block students from mutating courses (create / update / delete)."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, "role", None) in ("admin", "instructor")


class IsAuthenticatedReadOrCourseStaffWrite(BasePermission):
    """
    Safe methods: any authenticated user.
    Unsafe: admin or instructor of the related course (checked on object;
    create flows must call assert_can_edit_course in the view).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if user.role == "admin":
            return True
        course = _course_for_obj(obj)
        if course is None:
            return False
        return course.instructor_id == user.id


def learning_modules_queryset(user: CustomUser):
    """
    Modules the user may access (admin / instructor of or enrolled in course).
    Uses subqueries instead of materializing large course id lists in Python.
    """
    from .models import Module

    if not user.is_authenticated:
        return Module.objects.none()
    if getattr(user, "role", None) == "admin":
        return Module.objects.all()
    if user.role == "instructor":
        return Module.objects.filter(
            Q(course__instructor=user) | Q(course__enrollments__user=user)
        ).distinct()
    return Module.objects.filter(course__enrollments__user=user).distinct()


def learning_lessons_queryset(user: CustomUser):
    from .models import Lesson

    return Lesson.objects.filter(module__in=learning_modules_queryset(user))


def learning_contents_queryset(user: CustomUser):
    from .models import Content

    return Content.objects.filter(lesson__module__in=learning_modules_queryset(user))


def allowed_course_ids_for_learning(user: CustomUser):
    """Course IDs (legacy helper); prefer ``learning_*_queryset`` in hot paths."""
    return list(
        learning_modules_queryset(user)
        .values_list("course_id", flat=True)
        .distinct()
    )


def user_can_view_full_course(user, course) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.role == "admin":
        return True
    if course.instructor_id == user.id:
        return True
    from .models import Enrollment

    return Enrollment.objects.filter(user=user, course=course).exists()


class LearningContentAccess(BasePermission):
    """
    Read module/lesson/content: admin, course instructor, or enrolled student.
    Write: admin or instructor of that course (same as staff write on object).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        course = _course_for_obj(obj)
        if course is None:
            return False
        user = request.user
        if user.role == "admin":
            return True
        if course.instructor_id == user.id:
            return True
        if request.method in SAFE_METHODS:
            from .models import Enrollment

            return Enrollment.objects.filter(user=user, course=course).exists()
        return False


class IsGradeEditorOrReadOwn(BasePermission):
    """GET: student sees own grade; instructor sees grades for their courses. PATCH: instructor/admin only."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        course = obj.enrollment.course
        if user.role == "admin":
            return True
        if request.method in SAFE_METHODS:
            if course.instructor_id == user.id:
                return True
            return obj.enrollment.user_id == user.id
        if request.method in ("PATCH", "PUT"):
            return course.instructor_id == user.id or user.role == "admin"
        return False
