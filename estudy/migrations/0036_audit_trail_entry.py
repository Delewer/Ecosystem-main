from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0035_ai_usage_cost"),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditTrailEntry",
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
                ("event_type", models.CharField(max_length=50)),
                ("source", models.CharField(default="app", max_length=40)),
                ("hash_algorithm", models.CharField(default="sha256", max_length=20)),
                ("payload_hash", models.CharField(max_length=64)),
                (
                    "previous_hash",
                    models.CharField(blank=True, max_length=64, null=True),
                ),
                ("record_hash", models.CharField(max_length=64, unique=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=models.deletion.SET_NULL,
                        related_name="audit_trail_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-id",),
            },
        ),
        migrations.AddIndex(
            model_name="audittrailentry",
            index=models.Index(
                fields=["event_type", "created_at"],
                name="estudy_audit_event_created_idx",
            ),
        ),
    ]
