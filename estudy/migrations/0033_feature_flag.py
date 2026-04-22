from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "estudy",
            "0032_rename_event_type_created_idx_estudy_even_event_t_548230_idx_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="FeatureFlag",
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
                ("key", models.CharField(max_length=120, unique=True)),
                ("enabled", models.BooleanField(default=False)),
                (
                    "rollout_percentage",
                    models.PositiveIntegerField(
                        default=100,
                        validators=[MinValueValidator(0), MaxValueValidator(100)],
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("key",)},
        ),
    ]
