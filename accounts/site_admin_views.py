"""
REST data for the platform owner's admin shell (Next / SPA).
Only users passing ``IsPlatformAdmin`` (role ``admin`` or Django superuser).
"""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsPlatformAdmin

User = get_user_model()


class SiteAdminOverviewView(APIView):
    """
    Dashboard aggregates: user/course counts, newsletter size, unread notifications,
    and small “recent” lists for activity widgets.
    """

    permission_classes = [IsAuthenticated, IsPlatformAdmin]

    def get(self, request):
        from courses.models import (
            Course,
            Enrollment,
            Message,
            NewsletterSubscriber,
            Notification,
        )

        role_agg = User.objects.aggregate(
            users=Count("id"),
            admin=Count("id", filter=Q(role="admin")),
            instructor=Count("id", filter=Q(role="instructor")),
            student=Count("id", filter=Q(role="student")),
        )
        users_total = role_agg["users"] or 0
        users_by_role = {
            "admin": role_agg["admin"] or 0,
            "instructor": role_agg["instructor"] or 0,
            "student": role_agg["student"] or 0,
        }

        recent_users = [
            {
                "id": u["id"],
                "username": u["username"],
                "role": u["role"],
                "date_joined": u["date_joined"],
            }
            for u in User.objects.order_by("-date_joined").values(
                "id", "username", "role", "date_joined"
            )[:10]
        ]

        recent_enrollments = []
        for e in (
            Enrollment.objects.select_related("user", "course")
            .order_by("-enrolled_at")[:10]
        ):
            recent_enrollments.append(
                {
                    "id": e.id,
                    "enrolled_at": e.enrolled_at,
                    "user": {"id": e.user_id, "username": e.user.username},
                    "course": {
                        "id": e.course_id,
                        "title": e.course.title,
                        "slug": e.course.slug,
                    },
                }
            )

        recent_courses = []
        for c in (
            Course.objects.select_related("instructor")
            .order_by("-created_at")[:10]
        ):
            recent_courses.append(
                {
                    "id": c.id,
                    "title": c.title,
                    "slug": c.slug,
                    "instructor_id": c.instructor_id,
                    "instructor_username": c.instructor.username,
                    "created_at": c.created_at,
                }
            )

        return Response(
            {
                "counts": {
                    "users": users_total,
                    "users_by_role": users_by_role,
                    "courses": Course.objects.count(),
                    "enrollments": Enrollment.objects.count(),
                    "messages": Message.objects.count(),
                    "newsletter_subscribers": NewsletterSubscriber.objects.count(),
                    "unread_notifications": Notification.objects.filter(
                        read_at__isnull=True
                    ).count(),
                },
                "recent": {
                    "users": recent_users,
                    "enrollments": recent_enrollments,
                    "courses": recent_courses,
                },
            }
        )
