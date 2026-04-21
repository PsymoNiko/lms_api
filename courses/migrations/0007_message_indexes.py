from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0006_notification"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="message",
            index=models.Index(
                fields=["recipient", "read_at"],
                name="courses_msg_recipient_read_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(
                fields=["recipient", "sender", "course"],
                name="courses_msg_recip_send_course_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="message",
            index=models.Index(
                fields=["sender", "recipient", "created_at"],
                name="courses_msg_send_recip_created_idx",
            ),
        ),
    ]
