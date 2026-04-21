from decimal import Decimal

from django.db import migrations, models


def slugify_existing_courses(apps, schema_editor):
    from django.utils.text import slugify

    Course = apps.get_model("courses", "Course")
    for course in Course.objects.order_by("id"):
        if course.slug:
            continue
        base = slugify(course.title)[:200] or "course"
        candidate = base
        n = 0
        while Course.objects.filter(slug=candidate).exclude(pk=course.pk).exists():
            n += 1
            candidate = f"{base}-{n}"
        course.slug = candidate
        course.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0002_content_file_content_text_optional"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="category",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="course",
            name="price",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0.00"),
                max_digits=10,
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="thumbnail",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="course_thumbnails/",
            ),
        ),
        migrations.AddField(
            model_name="course",
            name="slug",
            field=models.SlugField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.RunPython(slugify_existing_courses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="course",
            name="slug",
            field=models.SlugField(
                blank=True,
                help_text="URL segment; generated from title if left empty.",
                max_length=255,
                unique=True,
            ),
        ),
        migrations.CreateModel(
            name="NewsletterSubscriber",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
