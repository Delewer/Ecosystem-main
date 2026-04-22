from __future__ import annotations

from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def merge_duplicate_subjects_and_fix_lessons(apps, schema_editor):
    Subject = apps.get_model("estudy", "Subject")
    Lesson = apps.get_model("estudy", "Lesson")

    # --- 1. Fix broken Python lesson (title/slug = "1") ---
    broken = Lesson.objects.filter(slug="1").first()
    if broken:
        broken.title = "Introducere în Python"
        broken.slug = "introducere-in-python"
        broken.excerpt = "Primii pași în lumea programării Python: variabile, tipuri și comenzi de bază."
        broken.content = (
            "Bun venit în Python!\n\n"
            "Python este unul dintre cele mai populare limbaje de programare din lume. "
            "Este simplu de citit, puternic și folosit în aplicații web, știința datelor și AI.\n\n"
            "În această lecție descoperim cum se declară variabile, cum se afișează text "
            "și cum funcționează tipurile de date de bază: int, str, float și bool."
        )
        broken.difficulty = "beginner"
        broken.age_bracket = "11-13"
        broken.xp_reward = 60
        broken.save()

    # --- 2. Merge duplicate Coding Quest subjects ---
    # Keep the first (lowest id) Coding Quest subject; reassign all lessons from the rest
    cq_subjects = list(Subject.objects.filter(name="Coding Quest").order_by("id"))
    if len(cq_subjects) > 1:
        primary = cq_subjects[0]
        for duplicate in cq_subjects[1:]:
            Lesson.objects.filter(subject=duplicate).update(subject=primary)
            duplicate.delete()

    # --- 3. Ensure canonical subjects exist ---
    subjects_to_create = [
        (
            "Python",
            "Programare Python de la zero: variabile, condiții, bucle și funcții.",
        ),
        ("Bazele Web", "HTML, CSS și JavaScript — fundațiile oricărui site modern."),
        (
            "Matematica pentru coderi",
            "Logică, algoritmi și gândire computațională prin matematică aplicată.",
        ),
    ]
    for name, description in subjects_to_create:
        Subject.objects.get_or_create(name=name, defaults={"description": description})


def reverse_migration(apps, schema_editor):
    pass  # irreversible data migration — noop on reverse


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0046_robotlablevelprogress_robotlabrun"),
    ]

    operations = [
        migrations.RunPython(
            merge_duplicate_subjects_and_fix_lessons,
            reverse_migration,
        ),
    ]
