from django.db import migrations

PYTHON_DESCRIPTION = (
    "Invata bazele Python pas cu pas: variabile, conditii, bucle si exercitii "
    "practice pentru primele tale programe."
)


def update_python_subject_description(apps, schema_editor):
    Subject = apps.get_model("estudy", "Subject")
    Subject.objects.filter(name="Python").update(description=PYTHON_DESCRIPTION)


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0060_merge_duplicate_coding_quest_subjects"),
    ]

    operations = [
        migrations.RunPython(
            update_python_subject_description, migrations.RunPython.noop
        ),
    ]
