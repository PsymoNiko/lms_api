from django.db.models import Count, Prefetch, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from accounts.models import CustomUser

from .messenger_service import build_conversation_summaries
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
from .ws_notify import push_json_to_user
from .permissions import (
    DenyStudentCourseWrite,
    IsAuthenticatedReadOrCourseStaffWrite,
    IsGradeEditorOrReadOwn,
    LearningContentAccess,
    learning_contents_queryset,
    learning_lessons_queryset,
    learning_modules_queryset,
    user_can_view_full_course,
)
from .serializers import (
    ContentSerializer,
    CourseDetailSerializer,
    CoursePublicDetailSerializer,
    CourseSerializer,
    CourseStudentSerializer,
    EnrollmentReadSerializer,
    EnrollmentRosterSerializer,
    GradeSerializer,
    LessonDetailSerializer,
    LessonListSerializer,
    MessageSerializer,
    ModuleListSerializer,
    NewsletterSubscribeSerializer,
    NotificationSerializer,
)


def assert_can_edit_course(user, course):
    if user.role == "admin":
        return
    if course.instructor_id != user.id:
        raise PermissionDenied(_("You do not manage this course."))


class PublicStatsView(APIView):
    """Anonymous-friendly counts for landing / social proof."""

    permission_classes = [AllowAny]

    def get(self, request):
        role_agg = CustomUser.objects.aggregate(
            learners=Count("id", filter=Q(role="student")),
            instructors=Count("id", filter=Q(role="instructor")),
        )
        return Response(
            {
                "courses_count": Course.objects.count(),
                "learners_count": role_agg["learners"] or 0,
                "instructors_count": role_agg["instructors"] or 0,
            }
        )


class NewsletterSubscribeView(generics.CreateAPIView):
    queryset = NewsletterSubscriber.objects.all()
    serializer_class = NewsletterSubscribeSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "newsletter"


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "head", "options"):
            return [AllowAny()]
        if self.action in ("enroll", "curriculum", "enrollments", "students"):
            return [IsAuthenticated()]
        return [
            IsAuthenticated(),
            DenyStudentCourseWrite(),
            IsAuthenticatedReadOrCourseStaffWrite(),
        ]

    def get_queryset(self):
        base = Course.objects.select_related("instructor")
        if self.action in ("retrieve", "curriculum", "enroll", "enrollments", "students"):
            base = base.prefetch_related(
                Prefetch(
                    "module_set",
                    queryset=Module.objects.order_by("id").prefetch_related(
                        Prefetch(
                            "lesson_set",
                            queryset=Lesson.objects.order_by("id").prefetch_related(
                                Prefetch(
                                    "content_set",
                                    queryset=Content.objects.order_by("order", "id"),
                                )
                            ),
                        )
                    ),
                )
            )
        qs = base.order_by("-created_at")
        if (
            self.action == "list"
            and self.request.user.is_authenticated
            and self.request.query_params.get("mine") == "1"
            and getattr(self.request.user, "role", None) in ("instructor", "admin")
        ):
            qs = qs.filter(instructor=self.request.user)
        return qs

    def retrieve(self, request, *args, **kwargs):
        """
        Full curriculum (lessons + contents) only for enrolled learners or course staff.
        Anonymous and other users get catalog metadata + outline only (`access_level` = outline).
        """
        instance = self.get_object()
        if user_can_view_full_course(request.user, instance):
            ser = CourseDetailSerializer(instance, context={"request": request})
        else:
            ser = CoursePublicDetailSerializer(instance, context={"request": request})
        return Response(ser.data)

    @action(detail=True, methods=["get"], url_path="curriculum")
    def curriculum(self, request, pk=None):
        """Full Modules → Lessons → Contents tree (PRD). Requires enrollment or staff."""
        course = self.get_object()
        if not user_can_view_full_course(request.user, course):
            raise PermissionDenied(
                _("You must be enrolled in this course to view the full curriculum.")
            )
        return Response(
            CourseDetailSerializer(course, context={"request": request}).data
        )

    @action(detail=True, methods=["post"], url_path="enroll")
    def enroll(self, request, pk=None):
        """Enroll the current user in this course (PRD)."""
        course = self.get_object()
        user = request.user
        if getattr(user, "role", None) not in ("student", "instructor", "admin"):
            return Response(
                {"detail": _("This account role cannot enroll in courses.")},
                status=status.HTTP_403_FORBIDDEN,
            )
        if course.instructor_id == user.id:
            return Response(
                {"detail": _("Instructors cannot enroll in their own course.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if Enrollment.objects.filter(user=user, course=course).exists():
            return Response(
                {"detail": _("Already enrolled.")},
                status=status.HTTP_400_BAD_REQUEST,
            )
        row = Enrollment.objects.create(user=user, course=course)
        return Response(
            EnrollmentReadSerializer(row, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="enrollments")
    def enrollments(self, request, pk=None):
        """Roster for instructors/admins (PRD instructor journey)."""
        course = self.get_object()
        assert_can_edit_course(request.user, course)
        rows = (
            Enrollment.objects.filter(course=course)
            .select_related("user", "grade")
            .order_by("enrolled_at")
        )
        return Response(
            EnrollmentRosterSerializer(
                rows, many=True, context={"request": request}
            ).data
        )

    @action(detail=True, methods=["get"], url_path="students")
    def students(self, request, pk=None):
        """P2: learners enrolled in this course (instructor / admin only)."""
        course = self.get_object()
        assert_can_edit_course(request.user, course)
        rows = (
            Enrollment.objects.filter(course=course)
            .select_related("user")
            .order_by("enrolled_at")
        )
        return Response(
            CourseStudentSerializer(
                rows, many=True, context={"request": request}
            ).data
        )

    def perform_create(self, serializer):
        serializer.save()


class MyEnrollmentViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """P1: current user's enrollments for «My learning» (`GET /api/v1/enrollments/`)."""

    serializer_class = EnrollmentReadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Enrollment.objects.filter(user=self.request.user)
            .select_related("course", "course__instructor")
            .order_by("-enrolled_at")
        )


class ModuleViewSet(viewsets.ModelViewSet):
    serializer_class = ModuleListSerializer
    permission_classes = [IsAuthenticated, LearningContentAccess]

    def get_queryset(self):
        qs = learning_modules_queryset(self.request.user).select_related(
            "course", "course__instructor"
        )
        course_id = self.request.query_params.get("course")
        if course_id is not None:
            qs = qs.filter(course_id=course_id)
        return qs.order_by("id")

    def perform_create(self, serializer):
        course = serializer.validated_data["course"]
        assert_can_edit_course(self.request.user, course)
        serializer.save()


class LessonViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, LearningContentAccess]

    def get_queryset(self):
        qs = learning_lessons_queryset(self.request.user).select_related(
            "module", "module__course", "module__course__instructor"
        )
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                Prefetch(
                    "content_set",
                    queryset=Content.objects.order_by("order", "id"),
                )
            )
        module_id = self.request.query_params.get("module")
        if module_id is not None:
            qs = qs.filter(module_id=module_id)
        return qs.order_by("id")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonDetailSerializer
        return LessonListSerializer

    def perform_create(self, serializer):
        module = serializer.validated_data["module"]
        assert_can_edit_course(self.request.user, module.course)
        serializer.save()


class ContentViewSet(viewsets.ModelViewSet):
    serializer_class = ContentSerializer
    permission_classes = [IsAuthenticated, LearningContentAccess]

    def get_queryset(self):
        qs = learning_contents_queryset(self.request.user).select_related(
            "lesson",
            "lesson__module",
            "lesson__module__course",
            "lesson__module__course__instructor",
        )
        lesson_id = self.request.query_params.get("lesson")
        if lesson_id is not None:
            qs = qs.filter(lesson_id=lesson_id)
        return qs.order_by("lesson", "order", "id")

    def perform_create(self, serializer):
        lesson = serializer.validated_data["lesson"]
        assert_can_edit_course(self.request.user, lesson.module.course)
        serializer.save()


class GradeViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = GradeSerializer
    permission_classes = [IsAuthenticated, IsGradeEditorOrReadOwn]
    http_method_names = ["get", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = Grade.objects.select_related(
            "enrollment__user", "enrollment__course", "enrollment__course__instructor"
        )
        course_id = self.request.query_params.get("course")
        if user.role == "admin":
            qs = qs.order_by("id")
        elif user.role == "instructor":
            qs = qs.filter(enrollment__course__instructor=user).order_by("id")
        else:
            qs = qs.filter(enrollment__user=user).order_by("id")
        if course_id is not None and user.role in ("admin", "instructor"):
            qs = qs.filter(enrollment__course_id=course_id)
        return qs


class MessageViewSet(
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """
    Messenger-style messaging.

    - ``GET /messages/conversations/`` — inbox: last activity per (peer, course), unread counts.
    - ``GET /messages/?peer=<id>`` — thread with direct messages only (no ``course`` in query).
    - ``GET /messages/?peer=<id>&course=<courseId>`` — thread scoped to a course.
    - ``GET /messages/?course=<id>`` — all messages in that course (legacy).
    - ``POST /messages/mark-read/`` — body ``{"peer": <id>, "course": null|id}`` (omit ``course`` = direct only).
    - ``POST /messages/<id>/read/`` — mark one received message read.
    - ``GET /messages/suggest-users/?q=ab`` — find users to start a chat (min 2 chars).
    """

    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        u = self.request.user
        qs = Message.objects.filter(Q(sender=u) | Q(recipient=u)).select_related(
            "sender", "recipient", "course"
        )
        peer = self.request.query_params.get("peer")
        course_param = self.request.query_params.get("course")

        if peer is not None:
            try:
                peer_id = int(peer)
            except (TypeError, ValueError):
                raise ValidationError({"peer": _("Invalid peer id.")})
            if peer_id == u.id:
                return Message.objects.none()
            qs = qs.filter(
                Q(sender_id=peer_id, recipient=u) | Q(recipient_id=peer_id, sender=u)
            )
            if "course" not in self.request.query_params:
                qs = qs.filter(course__isnull=True)
            else:
                if course_param is None or course_param == "":
                    qs = qs.filter(course__isnull=True)
                else:
                    try:
                        qs = qs.filter(course_id=int(course_param))
                    except (TypeError, ValueError):
                        raise ValidationError({"course": _("Invalid course id.")})
        elif course_param is not None and course_param != "":
            try:
                qs = qs.filter(course_id=int(course_param))
            except (TypeError, ValueError):
                raise ValidationError({"course": _("Invalid course id.")})

        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        msg = serializer.save(sender=self.request.user)
        push_json_to_user(
            msg.recipient_id,
            {
                "type": "message",
                "message": MessageSerializer(msg, context={"request": self.request}).data,
            },
        )

    @action(detail=False, methods=["get"], url_path="conversations")
    def conversations(self, request):
        rows = build_conversation_summaries(request.user, request)
        return Response({"results": rows})

    @action(detail=False, methods=["post"], url_path="mark-read")
    def mark_read(self, request):
        peer = request.data.get("peer")
        try:
            peer_id = int(peer)
        except (TypeError, ValueError):
            raise ValidationError({"peer": _("A valid peer user id is required.")})
        if peer_id == request.user.id:
            raise ValidationError({"peer": _("Invalid peer.")})

        unread = Message.objects.filter(
            sender_id=peer_id,
            recipient=request.user,
            read_at__isnull=True,
        )
        course_payload = None
        if "course" in request.data:
            c = request.data.get("course")
            if c is None or c == "":
                unread = unread.filter(course__isnull=True)
                course_payload = None
            else:
                try:
                    cid = int(c)
                except (TypeError, ValueError):
                    raise ValidationError({"course": _("Invalid course id.")})
                unread = unread.filter(course_id=cid)
                course_payload = cid
        else:
            unread = unread.filter(course__isnull=True)

        now = timezone.now()
        count = unread.update(read_at=now)
        push_json_to_user(
            peer_id,
            {
                "type": "messages_read",
                "reader_id": request.user.id,
                "course": course_payload,
                "count": count,
            },
        )
        return Response({"marked": count})

    @action(detail=True, methods=["post"], url_path="read")
    def read_one(self, request, pk=None):
        msg = self.get_object()
        if msg.recipient_id != request.user.id:
            raise PermissionDenied(_("Only the recipient can mark this message read."))
        if msg.read_at is None:
            msg.read_at = timezone.now()
            msg.save(update_fields=["read_at"])
            push_json_to_user(
                msg.sender_id,
                {
                    "type": "message_read",
                    "message_id": msg.id,
                    "reader_id": request.user.id,
                },
            )
        ser = MessageSerializer(msg, context={"request": request})
        return Response(ser.data)

    @action(detail=False, methods=["get"], url_path="suggest-users")
    def suggest_users(self, request):
        q = (request.query_params.get("q") or "").strip()
        if len(q) < 2:
            return Response({"results": []})
        from .serializers import UserBriefSerializer

        users = (
            CustomUser.objects.filter(
                Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
            )
            .exclude(pk=request.user.pk)
            .order_by("username")[:25]
        )
        return Response(
            {
                "results": UserBriefSerializer(
                    users, many=True, context={"request": request}
                ).data
            }
        )


class NotificationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    In-app notification feed (bell).

    - ``GET /notifications/`` — paginated list; ``?unread=1`` for unread only.
    - ``GET /notifications/unread-count/`` — ``{ "count": <int> }``.
    - ``POST /notifications/<id>/read/`` — mark one read.
    - ``POST /notifications/mark-all-read/`` — mark all read.
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Notification.objects.filter(user=self.request.user)
        if self.request.query_params.get("unread") in ("1", "true", "yes"):
            qs = qs.filter(read_at__isnull=True)
        return qs.order_by("-created_at")

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        n = Notification.objects.filter(user=request.user, read_at__isnull=True).count()
        return Response({"count": n})

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request):
        now = timezone.now()
        updated = Notification.objects.filter(
            user=request.user, read_at__isnull=True
        ).update(read_at=now)
        return Response({"marked": updated})

    @action(detail=True, methods=["post"], url_path="read")
    def read_one(self, request, pk=None):
        obj = self.get_object()
        if obj.read_at is None:
            obj.read_at = timezone.now()
            obj.save(update_fields=["read_at"])
        return Response(NotificationSerializer(obj, context={"request": request}).data)
