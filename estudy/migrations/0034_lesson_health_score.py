from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0033_feature_flag"),
    ]

    operations = [
        migrations.CreateModel(
            name="LessonHealthScore",
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
                    "score",
                    models.FloatField(
                        default=0.0,
                        validators=[MinValueValidator(0), MaxValueValidator(100)],
                    ),
                ),
                (
                    "quality_score",
                    models.FloatField(
                        default=0.0,
                        validators=[MinValueValidator(0), MaxValueValidator(100)],
                    ),
                ),
                (
                    "completion_rate",
                    models.FloatField(
                        default=0.0,
                        validators=[MinValueValidator(0), MaxValueValidator(100)],
                    ),
                ),
                (
                    "avg_rating",
                    models.FloatField(
                        default=0.0,
                        validators=[MinValueValidator(0), MaxValueValidator(5)],
                    ),
                ),
                (
                    "average_completion_time_minutes",
                    models.FloatField(blank=True, null=True),
                ),
                ("details", models.JSONField(blank=True, default=dict)),
                ("computed_at", models.DateTimeField(auto_now=True)),
                (
                    "lesson",
                    models.OneToOneField(
                        on_delete=models.CASCADE,
                        related_name="health_score",
                        to="estudy.lesson",
                    ),
                ),
            ],
            options={"ordering": ("-computed_at",)},
        ),
    ]
