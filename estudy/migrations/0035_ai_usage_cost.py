from decimal import Decimal

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0034_lesson_health_score"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIUsageCost",
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
                ("provider", models.CharField(default="internal", max_length=50)),
                (
                    "model_name",
                    models.CharField(default="keyword-hints", max_length=100),
                ),
                ("prompt_tokens", models.PositiveIntegerField(default=0)),
                ("completion_tokens", models.PositiveIntegerField(default=0)),
                ("total_tokens", models.PositiveIntegerField(default=0)),
                (
                    "cost",
                    models.DecimalField(
                        decimal_places=6, default=Decimal("0.000000"), max_digits=12
                    ),
                ),
                ("currency", models.CharField(default="USD", max_length=10)),
                ("is_estimated", models.BooleanField(default=True)),
                ("details", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "request",
                    models.OneToOneField(
                        on_delete=models.deletion.CASCADE,
                        related_name="usage_cost",
                        to="estudy.aihintrequest",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="ai_usage_costs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
