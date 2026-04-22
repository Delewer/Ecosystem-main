from django.db import migrations
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    Subject = apps.get_model("estudy", "Subject")
    used_slugs = set()
    for subject in Subject.objects.all():
        base = slugify(subject.name) or f"subject-{subject.pk}"
        slug = base
        counter = 1
        while slug in used_slugs:
            slug = f"{base}-{counter}"
            counter += 1
        subject.slug = slug
        subject.save(update_fields=["slug"])
        used_slugs.add(slug)


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0050_add_slug_and_coop_session"),
    ]

    operations = [
        migrations.RunPython(populate_slugs, migrations.RunPython.noop),
    ]
