from decimal import Decimal

from django.db import models
from django.utils.text import slugify

from accounts.models import CustomUser


def content_file_upload_to(instance, filename):
    return f"course_content/lesson_{instance.lesson_id}/{filename}"


class Course(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        help_text="URL segment; generated from title if left empty.",
    )
    description = models.TextField()
    thumbnail = models.ImageField(
        upload_to="course_thumbnails/",
        blank=True,
        null=True,
    )
    category = models.CharField(max_length=100, blank=True, default="")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200] or "course"
            candidate = base
            n = 0
            while Course.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                n += 1
                candidate = f"{base}-{n}"
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    CONTENT_TYPE = [
        ("text", "Text"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("document", "Document"),
    ]
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, choices=CONTENT_TYPE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Content(models.Model):
    CONTENT_TYPE = [
        ("text", "Text"),
        ("video", "Video"),
        ("audio", "Audio"),
        ("document", "Document"),
    ]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, choices=CONTENT_TYPE)
    content = models.TextField(blank=True)
    file = models.FileField(
        upload_to=content_file_upload_to,
        blank=True,
        null=True,
        help_text="Optional for video, audio, and document. Not used for text.",
    )
    order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.content_type == "text":
            if self.file:
                self.file.delete(save=False)
            self.file = None
        super().save(*args, **kwargs)


class Enrollment(models.Model):
    """Student (or learner) registered in a course (PRD many-to-many via junction)."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "course"),
                name="courses_enrollment_user_course_uniq",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} → {self.course_id}"


class Grade(models.Model):
    """Final or in-course grade per enrollment (PRD)."""

    enrollment = models.OneToOneField(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="grade",
    )
    score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
    )
    max_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("100.00"),
    )
    feedback = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Grade({self.enrollment_id})"


class Notification(models.Model):
    """In-app notification (bell); created from signals and optionally pushed over WebSocket."""

    class Kind(models.TextChoices):
        MESSAGE = "message", "Message"
        GRADE = "grade", "Grade"
        ENROLLMENT = "enrollment", "Enrollment"

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=32, choices=Kind.choices)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    payload = models.JSONField(default=dict, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("user", "created_at")),
            models.Index(fields=("user", "read_at")),
        ]

    def __str__(self):
        return f"{self.kind} → user {self.user_id}"


class Message(models.Model):
    """Simple internal message between users (PRD messaging)."""

    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="received_messages",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
    )
    body = models.TextField()
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self):
        return f"Message {self.pk} {self.sender_id}→{self.recipient_id}"
