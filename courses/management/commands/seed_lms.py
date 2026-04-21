"""
Rich demo data for local development and demos.
Run: python manage.py seed_lms
Clear + reseed: python manage.py seed_lms --clear
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from courses.models import (
    Content,
    Course,
    Enrollment,
    Grade,
    Lesson,
    Message,
    Module,
    NewsletterSubscriber,
)

User = get_user_model()

SEED_USERNAMES = (
    "seed_admin",
    "seed_instructor_maya",
    "seed_instructor_james",
    "seed_student_alice",
    "seed_student_bob",
    "seed_student_chloe",
)

SEED_COURSE_SLUGS = (
    "python-foundations-seed",
    "modern-web-django-seed",
    "data-literacy-sql-seed",
)

DEFAULT_PASSWORD = "seedpass123"


def _sync_user(username, *, email, first_name, last_name, role, is_staff=False, is_superuser=False):
    u, _ = User.objects.update_or_create(
        username=username,
        defaults={
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "role": role,
            "is_staff": is_staff,
            "is_superuser": is_superuser,
        },
    )
    u.set_password(DEFAULT_PASSWORD)
    u.save()
    return u


def _clear_seed():
    Course.objects.filter(slug__in=SEED_COURSE_SLUGS).delete()
    User.objects.filter(username__in=SEED_USERNAMES).delete()


def _ensure_users():
    admin = _sync_user(
        "seed_admin",
        email="admin@seed.local",
        first_name="Nina",
        last_name="Admin",
        role="admin",
        is_staff=True,
        is_superuser=True,
    )
    maya = _sync_user(
        "seed_instructor_maya",
        email="maya@seed.local",
        first_name="Maya",
        last_name="Chen",
        role="instructor",
        is_staff=True,
    )
    james = _sync_user(
        "seed_instructor_james",
        email="james@seed.local",
        first_name="James",
        last_name="Okonkwo",
        role="instructor",
        is_staff=True,
    )

    students = []
    for username, first, last, email in (
        ("seed_student_alice", "Alice", "Martinez", "alice@seed.local"),
        ("seed_student_bob", "Bob", "Kim", "bob@seed.local"),
        ("seed_student_chloe", "Chloe", "Dupont", "chloe@seed.local"),
    ):
        students.append(
            _sync_user(
                username,
                email=email,
                first_name=first,
                last_name=last,
                role="student",
                is_staff=False,
            )
        )

    maya.profile.bio = "Former staff engineer; 10+ years teaching Python and systems design."
    maya.profile.save(update_fields=["bio"])
    james.profile.bio = "Full-stack developer; Django since 1.4."
    james.profile.save(update_fields=["bio"])

    return admin, maya, james, students


def _build_course_python(instructor):
    course, created = Course.objects.get_or_create(
        slug="python-foundations-seed",
        defaults={
            "title": "Python Foundations for Real Projects",
            "description": (
                "A practical first course in Python: syntax, data structures, files, "
                "and small scripts you can run today. Assumes no prior programming experience."
            ),
            "category": "Programming",
            "price": Decimal("49.00"),
            "instructor": instructor,
        },
    )
    if not created:
        return course

    m1 = Module.objects.create(
        course=course,
        title="Getting started",
        description="Environment, REPL, and your first programs.",
    )
    m2 = Module.objects.create(
        course=course,
        title="Data and control flow",
        description="Lists, loops, functions, and reading data.",
    )

    l1 = Lesson.objects.create(
        module=m1,
        title="Why Python and how we work",
        content_type="text",
    )
    Content.objects.create(
        lesson=l1,
        title="Welcome",
        content_type="text",
        order=1,
        content=(
            "<h2>Welcome</h2><p>Python is readable, widely used, and a great first language. "
            "In this module you will install Python, use a terminal or IDE, and run short scripts.</p>"
            "<ul><li>Use Python 3.11+</li><li>Keep a notes file for commands you learn</li></ul>"
        ),
    )

    l2 = Lesson.objects.create(
        module=m1,
        title="Variables and types",
        content_type="text",
    )
    Content.objects.create(
        lesson=l2,
        title="Core concepts",
        content_type="text",
        order=1,
        content=(
            "<p>Variables are names bound to objects. Common types include <code>int</code>, "
            "<code>float</code>, <code>str</code>, <code>bool</code>, and containers like <code>list</code>.</p>"
            "<pre><code>>>> name = \"DevLearn\"\n>>> len(name)\n8</code></pre>"
        ),
    )

    l3 = Lesson.objects.create(
        module=m2,
        title="Lists and iteration",
        content_type="video",
    )
    Content.objects.create(
        lesson=l3,
        title="Loop patterns (video walkthrough)",
        content_type="video",
        order=1,
        content="https://www.youtube.com/watch?v=rfscVS0vtbw",
    )

    l4 = Lesson.objects.create(
        module=m2,
        title="Functions and reuse",
        content_type="text",
    )
    Content.objects.create(
        lesson=l4,
        title="Defining functions",
        content_type="text",
        order=1,
        content=(
            "<p>Functions bundle logic with parameters and return values. Prefer small, "
            "testable functions over long scripts.</p>"
            "<pre><code>def greet(name: str) -> str:\n    return f\"Hello, {name}!\"</code></pre>"
        ),
    )
    Content.objects.create(
        lesson=l4,
        title="Cheat sheet PDF (placeholder)",
        content_type="document",
        order=2,
        content="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
    )

    return course


def _build_course_django(instructor):
    course, created = Course.objects.get_or_create(
        slug="modern-web-django-seed",
        defaults={
            "title": "Modern Web Apps with Django",
            "description": (
                "Build a data-backed web application with Django 5: models, the admin, "
                "class-based views, forms, authentication, and deployment basics."
            ),
            "category": "Web",
            "price": Decimal("89.00"),
            "instructor": instructor,
        },
    )
    if not created:
        return course

    m1 = Module.objects.create(
        course=course,
        title="Django project anatomy",
        description="settings, URLs, apps, and the request cycle.",
    )
    m2 = Module.objects.create(
        course=course,
        title="Models and the ORM",
        description="Design relational data and query it efficiently.",
    )

    l1 = Lesson.objects.create(
        module=m1,
        title="From HTTP request to response",
        content_type="text",
    )
    Content.objects.create(
        lesson=l1,
        title="Request cycle",
        content_type="text",
        order=1,
        content=(
            "<p>Django maps URLs to views. Views can render templates, return JSON, or redirect. "
            "Middleware wraps the request for cross-cutting concerns (sessions, security headers).</p>"
        ),
    )

    l2 = Lesson.objects.create(
        module=m1,
        title="Project tour screencast",
        content_type="video",
    )
    Content.objects.create(
        lesson=l2,
        title="Tour",
        content_type="video",
        order=1,
        content="https://www.youtube.com/watch?v=2vjPBrBU-TM",
    )

    l3 = Lesson.objects.create(
        module=m2,
        title="Designing models",
        content_type="text",
    )
    Content.objects.create(
        lesson=l3,
        title="Fields and relationships",
        content_type="text",
        order=1,
        content=(
            "<p>Use <code>ForeignKey</code> for many-to-one, <code>ManyToManyField</code> when both sides "
            "relate to many. Add <code>__str__</code> on models for readable admin rows.</p>"
        ),
    )

    l4 = Lesson.objects.create(
        module=m2,
        title="Migrations mindset",
        content_type="audio",
    )
    Content.objects.create(
        lesson=l4,
        title="Podcast clip (placeholder URL)",
        content_type="audio",
        order=1,
        content="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    )

    return course


def _build_course_sql(instructor):
    course, created = Course.objects.get_or_create(
        slug="data-literacy-sql-seed",
        defaults={
            "title": "Data Literacy with SQL",
            "description": (
                "Read and write relational data with SQL: SELECT, JOINs, aggregations, "
                "and how indexes shape performance."
            ),
            "category": "Data",
            "price": Decimal("0.00"),
            "instructor": instructor,
        },
    )
    if not created:
        return course

    m1 = Module.objects.create(
        course=course,
        title="Querying tables",
        description="SELECT, WHERE, ORDER BY, LIMIT.",
    )

    l1 = Lesson.objects.create(
        module=m1,
        title="Your first SELECTs",
        content_type="text",
    )
    Content.objects.create(
        lesson=l1,
        title="Syntax",
        content_type="text",
        order=1,
        content=(
            "<pre><code>SELECT id, title, price\nFROM course\nWHERE price &lt; 100\nORDER BY title;</code></pre>"
            "<p>Prefer explicit column lists in application code; avoid <code>SELECT *</code> in hot paths.</p>"
        ),
    )

    l2 = Lesson.objects.create(
        module=m1,
        title="JOINs explained",
        content_type="text",
    )
    Content.objects.create(
        lesson=l2,
        title="Inner join pattern",
        content_type="text",
        order=1,
        content=(
            "<p>Join fact rows to dimension tables on keys. Start with inner joins; use left join "
            "when you must keep unmatched rows from the left side.</p>"
        ),
    )

    return course


def _enroll_and_grades(course, users, scores):
    for user, score in zip(users, scores):
        enr, created = Enrollment.objects.get_or_create(user=user, course=course)
        if score is not None:
            g, _ = Grade.objects.get_or_create(enrollment=enr)
            g.score = Decimal(str(score))
            g.feedback = "Great participation in seed data — keep building small projects."
            g.save(update_fields=["score", "feedback", "updated_at"])


def _messages(maya, james, alice, bob, courses):
    py, web, sql = courses
    if not Message.objects.filter(sender=maya, recipient=alice, course=py).exists():
        Message.objects.create(
            sender=maya,
            recipient=alice,
            course=py,
            body="Hi Alice — loved your questions in module 2. Try the extra list exercises when you can.",
        )
    if not Message.objects.filter(sender=alice, recipient=maya, course=py).exists():
        Message.objects.create(
            sender=alice,
            recipient=maya,
            course=py,
            body="Thanks Maya! Could we cover file I/O in the next office hours?",
        )
    if not Message.objects.filter(sender=james, recipient=bob, course=web).exists():
        Message.objects.create(
            sender=james,
            recipient=bob,
            course=web,
            body="Bob: your model diagram is on the right track. Consider a separate Profile table for avatar/bio.",
        )


class Command(BaseCommand):
    help = "Seed rich LMS demo data (users seed_*, three courses, enrollments, grades, messages)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove previously seeded courses and users (seed_* / slug *-seed) then re-insert.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing seed courses and users…")
            _clear_seed()

        admin, maya, james, students = _ensure_users()
        alice, bob, chloe = students

        py = _build_course_python(maya)
        web = _build_course_django(james)
        sql = _build_course_sql(maya)

        _enroll_and_grades(py, [alice, bob, chloe], [92.5, 88.0, None])
        _enroll_and_grades(web, [alice, bob], [None, 76.5])
        _enroll_and_grades(sql, [chloe], [95.0])

        _messages(maya, james, alice, bob, (py, web, sql))

        for email in ("news1@seed.local", "news2@seed.local", "lead@example.com"):
            NewsletterSubscriber.objects.get_or_create(email=email)

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        self.stdout.write(f"  Password for all seed users: {DEFAULT_PASSWORD}")
        self.stdout.write("  Users: " + ", ".join(SEED_USERNAMES))
        self.stdout.write("  Courses (slugs): " + ", ".join(SEED_COURSE_SLUGS))
