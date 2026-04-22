import django.db.models.deletion
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0012_add_indexes"),
    ]

    operations = [
        migrations.CreateModel(
            name="CodeExercise",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField()),
                (
                    "language",
                    models.CharField(
                        choices=[
                            ("python", "Python"),
                            ("javascript", "JavaScript"),
                            ("html", "HTML/CSS"),
                            ("sql", "SQL"),
                        ],
                        default="python",
                        max_length=20,
                    ),
                ),
                ("starter_code", models.TextField(default="# Write your code here\n")),
                ("solution", models.TextField(blank=True)),
                ("hints", models.JSONField(blank=True, default=list)),
                ("test_cases", models.JSONField(blank=True, default=list)),
                (
                    "difficulty_level",
                    models.IntegerField(
                        default=1,
                        validators=[MinValueValidator(1), MaxValueValidator(5)],
                    ),
                ),
                ("points", models.PositiveIntegerField(default=10)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "lesson",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="code_exercises",
                        to="estudy.lesson",
                    ),
                ),
            ],
            options={
                "ordering": ("lesson", "order", "id"),
            },
        ),
        migrations.CreateModel(
            name="CodeSubmission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.TextField()),
                ("passed_tests", models.PositiveIntegerField(default=0)),
                ("total_tests", models.PositiveIntegerField(default=0)),
                ("is_correct", models.BooleanField(default=False)),
                ("execution_time_ms", models.PositiveIntegerField(default=0)),
                ("output", models.TextField(blank=True)),
                ("error_message", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                (
                    "exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submissions",
                        to="estudy.codeexercise",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="code_submissions",
                        to="auth.user",
                    ),
                ),
            ],
            options={
                "ordering": ("-submitted_at", "id"),
            },
        ),
        migrations.AddIndex(
            model_name="codesubmission",
            index=models.Index(fields=["user", "exercise"], name="est_cs_user_ex_idx"),
        ),
    ]
