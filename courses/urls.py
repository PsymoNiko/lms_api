from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ContentViewSet,
    CourseViewSet,
    GradeViewSet,
    LessonViewSet,
    MessageViewSet,
    ModuleViewSet,
    MyEnrollmentViewSet,
    NewsletterSubscribeView,
    NotificationViewSet,
    PublicStatsView,
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"modules", ModuleViewSet, basename="module")
router.register(r"lessons", LessonViewSet, basename="lesson")
router.register(r"contents", ContentViewSet, basename="content")
router.register(r"enrollments", MyEnrollmentViewSet, basename="enrollment")
router.register(r"grades", GradeViewSet, basename="grade")
router.register(r"messages", MessageViewSet, basename="message")
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path("api/v1/stats/", PublicStatsView.as_view(), name="public-stats"),
    path(
        "api/v1/newsletter/",
        NewsletterSubscribeView.as_view(),
        name="newsletter-subscribe",
    ),
    path("api/v1/", include(router.urls)),
]
