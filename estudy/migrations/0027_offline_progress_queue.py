from __future__ import annotations

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("estudy", "0026_event_log"),
    ]

    operations = [
        migrations.CreateModel(
            name="OfflineProgressQueue",
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
                ("payload", models.JSONField(default=dict)),
                ("synced", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("synced_at", models.DateTimeField(blank=True, null=True)),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offline_progress_queue",
                        to="estudy.lesson",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="offline_progress_queue",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="offlineprogressqueue",
            index=models.Index(
                fields=["user", "synced"], name="offline_user_synced_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="offlineprogressqueue",
            index=models.Index(
                fields=["lesson", "synced"], name="offline_lesson_synced_idx"
            ),
        ),
    ]
