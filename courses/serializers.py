from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from accounts.models import CustomUser
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


class UserBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ("id", "username", "email", "role")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and not request.user.is_authenticated:
            data.pop("email", None)
        return data


class ContentSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Content
        fields = (
            "id",
            "lesson",
            "title",
            "content_type",
            "content",
            "file",
            "file_url",
            "order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_file_url(self, obj):
        if not obj.file:
            return None
        url = obj.file.url
        if url.startswith("http"):
            return url
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url

    def validate(self, attrs):
        inst = self.instance
        ctype = attrs.get("content_type")
        if ctype is None:
            if not inst:
                raise serializers.ValidationError(
                    {"content_type": _("This field is required.")}
                )
            ctype = inst.content_type

        if "content" in attrs:
            text = (attrs.get("content") or "").strip()
        elif inst:
            text = (inst.content or "").strip()
        else:
            text = ""

        if "file" in attrs:
            uploaded = attrs.get("file")
        elif inst:
            uploaded = inst.file
        else:
            uploaded = None

        if ctype == "text":
            if not text:
                raise serializers.ValidationError(
                    {"content": _("Text content is required.")}
                )
            if uploaded:
                raise serializers.ValidationError(
                    {"file": _("Do not upload a file when the type is text.")}
                )
        else:
            if not text and not uploaded:
                raise serializers.ValidationError(
                    _("Enter a URL / embed text or upload a file (or both).")
                )
        return attrs


class LessonListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = (
            "id",
            "module",
            "title",
            "content_type",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class LessonDetailSerializer(serializers.ModelSerializer):
    contents = ContentSerializer(source="content_set", many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = (
            "id",
            "module",
            "title",
            "content_type",
            "contents",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class ModuleListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = (
            "id",
            "course",
            "title",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class ModuleDetailSerializer(serializers.ModelSerializer):
    lessons = LessonDetailSerializer(source="lesson_set", many=True, read_only=True)

    class Meta:
        model = Module
        fields = (
            "id",
            "course",
            "title",
            "description",
            "lessons",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")


class LessonPublicOutlineSerializer(serializers.ModelSerializer):
    """Syllabus only: no contents (text, URLs, files)."""

    class Meta:
        model = Lesson
        fields = (
            "id",
            "module",
            "title",
            "content_type",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class ModulePublicOutlineSerializer(serializers.ModelSerializer):
    lessons = LessonPublicOutlineSerializer(source="lesson_set", many=True, read_only=True)

    class Meta:
        model = Module
        fields = (
            "id",
            "course",
            "title",
            "description",
            "lessons",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class CoursePublicDetailSerializer(serializers.ModelSerializer):
    """Catalog / landing detail: metadata + outline; full blocks require enrollment or staff."""

    instructor_detail = UserBriefSerializer(source="instructor", read_only=True)
    modules = ModulePublicOutlineSerializer(source="module_set", many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField(read_only=True)
    access_level = serializers.SerializerMethodField()
    curriculum_requires_enrollment = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "thumbnail",
            "thumbnail_url",
            "category",
            "price",
            "instructor",
            "instructor_detail",
            "modules",
            "access_level",
            "curriculum_requires_enrollment",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_thumbnail_url(self, obj):
        if not obj.thumbnail:
            return None
        url = obj.thumbnail.url
        if url.startswith("http"):
            return url
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_access_level(self, obj):
        return "outline"

    def get_curriculum_requires_enrollment(self, obj):
        return True


class CourseSerializer(serializers.ModelSerializer):
    instructor_detail = UserBriefSerializer(source="instructor", read_only=True)
    thumbnail_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "thumbnail",
            "thumbnail_url",
            "category",
            "price",
            "instructor",
            "instructor_detail",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")
        extra_kwargs = {"instructor": {"required": False}}

    def get_thumbnail_url(self, obj):
        if not obj.thumbnail:
            return None
        url = obj.thumbnail.url
        if url.startswith("http"):
            return url
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url

    def validate(self, attrs):
        request = self.context.get("request")
        user = request.user if request else None
        if not user or not user.is_authenticated:
            return attrs
        if self.instance is None:
            if user.role == "student":
                raise serializers.ValidationError(
                    _("Students cannot create courses.")
                )
            inst = attrs.get("instructor")
            if user.role != "admin":
                attrs["instructor"] = user
            elif inst is None:
                raise serializers.ValidationError(
                    {"instructor": _("Instructor is required for this action.")}
                )
        return attrs

    def validate_instructor(self, instructor):
        request = self.context.get("request")
        user = request.user if request else None
        if not user or not user.is_authenticated:
            return instructor
        if user.role != "admin" and instructor.pk != user.pk:
            raise serializers.ValidationError(
                _("You may only assign yourself as instructor.")
            )
        return instructor


class CourseDetailSerializer(serializers.ModelSerializer):
    instructor_detail = UserBriefSerializer(source="instructor", read_only=True)
    modules = ModuleDetailSerializer(source="module_set", many=True, read_only=True)
    thumbnail_url = serializers.SerializerMethodField(read_only=True)
    access_level = serializers.SerializerMethodField()
    curriculum_requires_enrollment = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "slug",
            "description",
            "thumbnail",
            "thumbnail_url",
            "category",
            "price",
            "instructor",
            "instructor_detail",
            "modules",
            "access_level",
            "curriculum_requires_enrollment",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def get_thumbnail_url(self, obj):
        if not obj.thumbnail:
            return None
        url = obj.thumbnail.url
        if url.startswith("http"):
            return url
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(url)
        return url

    def get_access_level(self, obj):
        return "full"

    def get_curriculum_requires_enrollment(self, obj):
        return False


class EnrollmentReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ("id", "user", "course", "enrolled_at")
        read_only_fields = ("id", "user", "course", "enrolled_at")


class CourseStudentSerializer(serializers.ModelSerializer):
    """Instructor roster: enrolled learner + timestamp."""

    user = UserBriefSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ("user", "enrolled_at")
        read_only_fields = fields


class GradeMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ("id", "score", "max_score", "feedback", "updated_at")


class EnrollmentRosterSerializer(serializers.ModelSerializer):
    user = UserBriefSerializer(read_only=True)
    grade = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ("id", "user", "course", "enrolled_at", "grade")
        read_only_fields = ("id", "user", "course", "enrolled_at", "grade")

    def get_grade(self, obj):
        try:
            g = obj.grade
        except ObjectDoesNotExist:
            return None
        return GradeMiniSerializer(g, context=self.context).data


class GradeSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(
        source="enrollment.course.title", read_only=True
    )
    student_username = serializers.CharField(
        source="enrollment.user.username", read_only=True
    )

    class Meta:
        model = Grade
        fields = (
            "id",
            "enrollment",
            "course_title",
            "student_username",
            "score",
            "max_score",
            "feedback",
            "updated_at",
        )
        read_only_fields = ("id", "enrollment", "course_title", "student_username", "updated_at")


class MessageSerializer(serializers.ModelSerializer):
    read = serializers.SerializerMethodField()
    sender_detail = UserBriefSerializer(source="sender", read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id",
            "sender",
            "sender_detail",
            "recipient",
            "course",
            "body",
            "read",
            "read_at",
            "is_mine",
            "created_at",
        )
        read_only_fields = (
            "id",
            "sender",
            "sender_detail",
            "read",
            "read_at",
            "created_at",
            "is_mine",
        )

    def get_read(self, obj):
        return obj.read_at is not None

    def get_is_mine(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return obj.sender_id == request.user.id

    def validate_body(self, value):
        text = (value or "").strip()
        if not text:
            raise serializers.ValidationError(_("Message cannot be empty."))
        if len(text) > 10_000:
            raise serializers.ValidationError(_("Message is too long (max 10000 characters)."))
        return text

    def validate_course(self, course):
        if course is None:
            return course
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return course
        if getattr(user, "role", None) == "admin":
            return course
        if course.instructor_id == user.id:
            return course
        if Enrollment.objects.filter(user=user, course=course).exists():
            return course
        raise serializers.ValidationError(
            _("You may only attach a course context to courses you teach or are enrolled in.")
        )

    def validate_recipient(self, value):
        request = self.context.get("request")
        if request and value.pk == request.user.pk:
            raise serializers.ValidationError(_("You cannot message yourself."))
        return value


class NotificationSerializer(serializers.ModelSerializer):
    read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id",
            "kind",
            "title",
            "body",
            "payload",
            "read",
            "read_at",
            "created_at",
        )
        read_only_fields = (
            "id",
            "kind",
            "title",
            "body",
            "payload",
            "read",
            "read_at",
            "created_at",
        )

    def get_read(self, obj):
        return obj.read_at is not None


class NewsletterSubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSubscriber
        fields = ("email",)

    def validate_email(self, value):
        return value.strip().lower()

    def create(self, validated_data):
        email = validated_data["email"]
        if NewsletterSubscriber.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                {"email": _("This address is already subscribed.")}
            )
        return NewsletterSubscriber.objects.create(email=email)
