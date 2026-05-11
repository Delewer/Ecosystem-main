import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("estudy", "0061_update_python_subject_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="LearnerCheckIn",
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
                    "mood",
                    models.CharField(
                        choices=[
                            ("understood", "Understood"),
                            ("needs_help", "Needs help"),
                        ],
                        default="understood",
                        max_length=20,
                    ),
                ),
                (
                    "difficulty",
                    models.CharField(
                        choices=[
                            ("too_easy", "Too easy"),
                            ("just_right", "Just right"),
                            ("too_hard", "Too hard"),
                        ],
                        default="just_right",
                        max_length=20,
                    ),
                ),
                ("help_requested", models.BooleanField(db_index=True, default=False)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="learner_checkins",
                        to="estudy.lesson",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="learner_checkins",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-updated_at",),
                "unique_together": {("user", "lesson")},
            },
        ),
        migrations.AddIndex(
            model_name="learnercheckin",
            index=models.Index(
                fields=["user", "help_requested"], name="est_lci_user_help_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="learnercheckin",
            index=models.Index(
                fields=["lesson", "updated_at"], name="est_lci_lesson_idx"
            ),
        ),
    ]
