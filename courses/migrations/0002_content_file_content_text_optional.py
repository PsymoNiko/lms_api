from django.db import migrations, models

import courses.models


class Migration(migrations.Migration):

    dependencies = [
        ("courses", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="content",
            name="file",
            field=models.FileField(
                blank=True,
                help_text="Optional for video, audio, and document. Not used for text.",
                null=True,
                upload_to=courses.models.content_file_upload_to,
            ),
        ),
        migrations.AlterField(
            model_name="content",
            name="content",
            field=models.TextField(blank=True),
        ),
    ]
