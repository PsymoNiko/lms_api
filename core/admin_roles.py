"""Shared helpers for role-based Django admin."""


def user_is_platform_admin(user) -> bool:
    return bool(
        user.is_authenticated
        and user.is_active
        and user.is_staff
        and (user.is_superuser or getattr(user, "role", None) == "admin")
    )


def user_is_instructor(user) -> bool:
    return bool(
        user.is_authenticated
        and user.is_active
        and user.is_staff
        and getattr(user, "role", None) == "instructor"
    )


def user_can_access_staff_admin(user) -> bool:
    """Instructor or platform admin with staff flag (students: no admin UI)."""
    return bool(
        user.is_authenticated
        and user.is_active
        and user.is_staff
        and getattr(user, "role", None) in ("admin", "instructor")
    )
