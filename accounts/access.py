"""Permission flags for the current user — keep in sync with API + Django admin rules."""

from __future__ import annotations

from core.admin_roles import user_can_access_staff_admin


def access_flags_for_user(user) -> dict[str, bool]:
    """
    Booleans the frontend can use for routing and conditional UI.
    Course-level checks (e.g. own-course only) still belong in the API; these are role-wide.
    """
    role = getattr(user, "role", None)
    if role not in ("admin", "instructor", "student"):
        role = "student"
    is_platform_admin = bool(user.is_superuser or role == "admin")
    staff_courses = role in ("admin", "instructor")
    return {
        "can_manage_users": is_platform_admin,
        "can_access_site_owner_panel": is_platform_admin,
        "can_write_courses": staff_courses,
        "can_use_mine_courses_query": staff_courses,
        "can_enroll_in_courses": role in ("student", "instructor", "admin"),
        "can_write_learning_content": staff_courses,
        "can_view_grade_rosters": staff_courses,
        "can_access_django_admin": user_can_access_staff_admin(user),
    }


def me_payload(user) -> dict:
    role = getattr(user, "role", None)
    if role not in ("admin", "instructor", "student"):
        role = "student"
    return {
        "id": user.pk,
        "username": user.username,
        "email": user.email or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "role": role,
        "is_staff": bool(user.is_staff),
        "is_superuser": bool(user.is_superuser),
        "access": access_flags_for_user(user),
    }
