from __future__ import annotations

from django.db import migrations


def populate_lessons(apps, schema_editor):
    Lesson = apps.get_model("estudy", "Lesson")
    Skill = apps.get_model("estudy", "Skill")
    LessonObjective = apps.get_model("estudy", "LessonObjective")
    LessonReflectionPrompt = apps.get_model("estudy", "LessonReflectionPrompt")
    LessonMedia = apps.get_model("estudy", "LessonMedia")
    LessonMediaSegment = apps.get_model("estudy", "LessonMediaSegment")

    default_skills = [
        (
            "curiosity",
            "Curiozitate",
            "Învățăm să punem întrebări și să căutăm răspunsuri",
        ),
        (
            "creative-thinking",
            "Gândire creativă",
            "Găsim mai multe idei pentru aceeași provocare",
        ),
        (
            "communication",
            "Comunicare clară",
            "Ne exprimăm ideile pe înțelesul tuturor",
        ),
        (
            "problem-solving",
            "Rezolvare de probleme",
            "Împărțim sarcina în pași simpli și logici",
        ),
        (
            "digital-safety",
            "Siguranță digitală",
            "Lucrăm responsabil și protejat în mediul online",
        ),
    ]

    skill_objects = []
    for slug, title, description in default_skills:
        skill, _ = Skill.objects.get_or_create(
            slug=slug,
            defaults={"title": title, "description": description},
        )
        skill_objects.append(skill)

    titles = [
        "Startul aventurii",
        "Misiunea practică",
        "Recapitulare și wow",
    ]

    for lesson in Lesson.objects.all():
        updates = {}
        if not getattr(lesson, "warmup_prompt", None):
            updates[
                "warmup_prompt"
            ] = f"Imaginează-ți că tema «{lesson.title}» te ajută într-o aventură. Cum ai folosi-o?"
        if not getattr(lesson, "story_anchor", None):
            updates[
                "story_anchor"
            ] = f"Astăzi explorăm tema «{lesson.title}» ca niște inventatori curioși."
        if not getattr(lesson, "home_extension", None):
            updates[
                "home_extension"
            ] = f"Povestește acasă ce ai învățat la lecția «{lesson.title}» și imaginați împreună o mini provocare."
        prompts = [
            p.strip()
            for p in (getattr(lesson, "discussion_prompts", []) or [])
            if str(p).strip()
        ]
        if not prompts:
            updates["discussion_prompts"] = [
                f"Ce te surprinde la tema «{lesson.title}»?",
                "Cum ai explica această idee unui coleg mai mic?",
                "Unde ai întâlnit acest concept în viața de zi cu zi?",
            ]
        tracks = [
            t.strip()
            for t in (getattr(lesson, "content_tracks", []) or [])
            if str(t).strip()
        ]
        if not tracks:
            updates["content_tracks"] = ["Traseu de bază", "Bonus pentru exploratori"]
        if not getattr(lesson, "collaboration_mode", None):
            updates["collaboration_mode"] = "small_group"
        if updates:
            for field, value in updates.items():
                setattr(lesson, field, value)
            lesson.save(update_fields=list(updates.keys()))

        if skill_objects and lesson.skills.count() == 0:
            index = (lesson.pk or 0) % len(skill_objects)
            lesson.skills.add(
                skill_objects[index], skill_objects[(index + 1) % len(skill_objects)]
            )

        if LessonObjective.objects.filter(lesson=lesson).count() == 0:
            payloads = [
                (
                    f"Să descoperim cum se regăsește tema «{lesson.title}» în viața de zi cu zi.",
                    "Context",
                    "Pot să dau un exemplu din viața mea",
                ),
                (
                    "Să aplicăm noile cunoștințe într-o mini sarcină practică.",
                    "Practică",
                    "Rezolv pașii propuși și verific rezultatul",
                ),
                (
                    "Să formulăm un mesaj clar și să-l împărtășim cu colegii.",
                    "Comunicare",
                    "Explic ideea cu propriile cuvinte",
                ),
            ]
            LessonObjective.objects.bulk_create(
                [
                    LessonObjective(
                        lesson=lesson,
                        description=desc,
                        focus_area=focus,
                        success_criteria=criteria,
                        order=index,
                    )
                    for index, (desc, focus, criteria) in enumerate(payloads)
                ]
            )

        if LessonReflectionPrompt.objects.filter(lesson=lesson).count() == 0:
            LessonReflectionPrompt.objects.bulk_create(
                [
                    LessonReflectionPrompt(
                        lesson=lesson,
                        prompt="Cum te simți după lecție?",
                        format="scale",
                        scale_labels=[
                            "Am nevoie de ajutor",
                            "Mă descurc",
                            "Pot explica și altora",
                        ],
                        order=0,
                    ),
                    LessonReflectionPrompt(
                        lesson=lesson,
                        prompt=f"Ce descoperire nouă ai făcut despre tema «{lesson.title}»?",
                        format="text",
                        order=1,
                    ),
                ]
            )

        try:
            media = LessonMedia.objects.get(lesson=lesson)
        except LessonMedia.DoesNotExist:
            media = None
        if media and media.segments.count() == 0:
            total = (
                media.video_duration_seconds
                or media.audio_duration_seconds
                or media.slides_count * 45
            )
            if total <= 0:
                total = 180
            step = max(total // 3, 1)
            checkpoints = [0, min(step, total), min(step * 2, total), total]
            LessonMediaSegment.objects.bulk_create(
                [
                    LessonMediaSegment(
                        media=media,
                        title=titles[i],
                        description=f"Segmentul {i + 1} din lecția «{lesson.title}».",
                        start_seconds=checkpoints[i],
                        end_seconds=checkpoints[i + 1],
                        order=i,
                    )
                    for i in range(3)
                ]
            )


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0019_skill_lesson_collaboration_mode_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_lessons, migrations.RunPython.noop),
    ]
