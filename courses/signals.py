from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Enrollment, Grade, Message, Notification
from .notifications_service import create_notification, preview_text


@receiver(post_save, sender=Enrollment)
def create_grade_for_enrollment(sender, instance, created, **kwargs):
    if created:
        Grade.objects.get_or_create(enrollment=instance)


@receiver(post_save, sender=Enrollment)
def notify_instructor_on_enrollment(sender, instance, created, **kwargs):
    if not created:
        return
    course = instance.course
    instructor = course.instructor
    student = instance.user
    if student.id == instructor.id:
        return
    name = student.get_full_name() or student.username
    create_notification(
        instructor,
        kind=Notification.Kind.ENROLLMENT,
        title=f"New enrollment: {course.title}",
        body=f"{name} joined your course.",
        payload={
            "enrollment_id": instance.id,
            "course_id": course.id,
            "student_id": student.id,
        },
    )


@receiver(post_save, sender=Message)
def notify_recipient_on_message(sender, instance, created, **kwargs):
    if not created:
        return
    sender_user = instance.sender
    name = sender_user.get_full_name() or sender_user.username
    create_notification(
        instance.recipient,
        kind=Notification.Kind.MESSAGE,
        title=f"New message from {name}",
        body=preview_text(instance.body),
        payload={
            "message_id": instance.id,
            "sender_id": instance.sender_id,
            "course_id": instance.course_id,
        },
    )


@receiver(post_save, sender=Grade)
def notify_student_on_grade(sender, instance, created, **kwargs):
    student = instance.enrollment.user
    course = instance.enrollment.course
    if created:
        if instance.score is None and not (instance.feedback or "").strip():
            return
    elif instance.score is None and not (instance.feedback or "").strip():
        return
    score_txt = ""
    if instance.score is not None:
        score_txt = f"Score: {instance.score} / {instance.max_score}. "
    fb = (instance.feedback or "").strip()
    body = score_txt + (preview_text(fb, 300) if fb else "")
    create_notification(
        student,
        kind=Notification.Kind.GRADE,
        title=f"Grade update: {course.title}",
        body=body or "Your grade was updated.",
        payload={
            "grade_id": instance.id,
            "course_id": course.id,
            "enrollment_id": instance.enrollment_id,
        },
    )
