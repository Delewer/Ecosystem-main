from __future__ import annotations

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("estudy", "0025_rubrics_and_project_evaluations"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventLog",
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
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("login", "Login"),
                            ("lesson_view", "Lesson view"),
                            ("test_start", "Test start"),
                            ("test_submit", "Test submit"),
                            ("achievement_awarded", "Achievement awarded"),
                        ],
                        max_length=50,
                    ),
                ),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name="event_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddIndex(
            model_name="eventlog",
            index=models.Index(
                fields=["event_type", "created_at"], name="event_type_created_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="eventlog",
            index=models.Index(
                fields=["user", "created_at"], name="event_user_created_idx"
            ),
        ),
    ]
