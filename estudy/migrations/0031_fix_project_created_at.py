from django.db import migrations, models
from django.utils import timezone


def fill_project_created_at(apps, schema_editor):
    Project = apps.get_model("estudy", "Project")
    now = timezone.now()
    Project.objects.filter(created_at__isnull=True).update(created_at=now)


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0030_classrooms_parent_community"),
    ]

    operations = [
        migrations.RunPython(
            fill_project_created_at, reverse_code=migrations.RunPython.noop
        ),
        migrations.AlterField(
            model_name="project",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
