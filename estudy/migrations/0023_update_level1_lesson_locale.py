from __future__ import annotations

from django.db import migrations


def update_level1_content(apps, schema_editor):
    Lesson = apps.get_model("estudy", "Lesson")
    LessonObjective = apps.get_model("estudy", "LessonObjective")
    LessonReflectionPrompt = apps.get_model("estudy", "LessonReflectionPrompt")
    Skill = apps.get_model("estudy", "Skill")

    lesson = Lesson.objects.filter(
        title__iexact="Nivel 1 · Prieteni cu variabilele"
    ).first()
    if not lesson:
        return

    updates = {
        "warmup_prompt": "Imaginează-ți că tema «Nivel 1 · Prieteni cu variabilele» te ajută într-o aventură. Cum ai folosi-o?",
        "discussion_prompts": [
            "Ce te surprinde la tema «Nivel 1 · Prieteni cu variabilele»?",
            "Cum ai explica această idee unui coleg mai mic?",
            "Unde ai întâlnit acest concept în viața de zi cu zi?",
        ],
        "home_extension": "Povestește acasă ce ai învățat la lecția «Nivel 1 · Prieteni cu variabilele» și imaginați împreună o mini provocare.",
        "story_anchor": "Astăzi explorăm tema «Nivel 1 · Prieteni cu variabilele» ca niște inventatori curioși.",
        "content_tracks": [
            "Traseu de bază",
            "Bonus pentru exploratori",
        ],
        "collaboration_mode": "solo",
    }

    dirty_fields: list[str] = []
    for field, value in updates.items():
        current = getattr(lesson, field, None)
        if current != value and value is not None:
            setattr(lesson, field, value)
            dirty_fields.append(field)

    if dirty_fields:
        lesson.save(update_fields=dirty_fields)

    objective_payloads = [
        (
            "Să descoperim cum se regăsește tema «Nivel 1 · Prieteni cu variabilele» în viața de zi cu zi.",
            "Context",
            "Pot să dau un exemplu din viața mea",
        ),
        (
            "Să aplicăm noile cunoștințe într-o mini sarcină practică.",
            "Practică",
            "Urmez pașii exercițiului propus",
        ),
        (
            "Să formulăm propriul mesaj și să-l împărtășim cu colegii.",
            "Comunicare",
            "Explic ideea cu propriile cuvinte",
        ),
    ]

    objectives = list(
        LessonObjective.objects.filter(lesson=lesson).order_by("order", "id")
    )
    for index, payload in enumerate(objective_payloads):
        if index < len(objectives):
            obj = objectives[index]
            desc, focus, criteria = payload
            dirty_obj_fields: list[str] = []
            if obj.description != desc:
                obj.description = desc
                dirty_obj_fields.append("description")
            if obj.focus_area != focus:
                obj.focus_area = focus
                dirty_obj_fields.append("focus_area")
            if obj.success_criteria != criteria:
                obj.success_criteria = criteria
                dirty_obj_fields.append("success_criteria")
            if dirty_obj_fields:
                obj.save(update_fields=dirty_obj_fields)
        else:
            LessonObjective.objects.create(
                lesson=lesson,
                description=payload[0],
                focus_area=payload[1],
                success_criteria=payload[2],
                order=index,
            )

    prompts = list(
        LessonReflectionPrompt.objects.filter(lesson=lesson).order_by("order", "id")
    )
    if prompts:
        primary = prompts[0]
        primary_dirty: list[str] = []
        desired_prompt = "Cum te simți după lecție?"
        desired_scale = [
            "Am nevoie de ajutor",
            "Mă descurc",
            "Pot explica și altora",
        ]
        if primary.prompt != desired_prompt:
            primary.prompt = desired_prompt
            primary_dirty.append("prompt")
        if getattr(primary, "scale_labels", None) != desired_scale:
            primary.scale_labels = desired_scale
            primary_dirty.append("scale_labels")
        if getattr(primary, "format", "") != "scale":
            primary.format = "scale"
            primary_dirty.append("format")
        if primary_dirty:
            primary.save(update_fields=primary_dirty)

    if len(prompts) > 1:
        secondary = prompts[1]
        if (
            secondary.prompt
            != "Ce descoperire nouă ai făcut despre tema «Nivel 1 · Prieteni cu variabilele»?"
        ):
            secondary.prompt = "Ce descoperire nouă ai făcut despre tema «Nivel 1 · Prieteni cu variabilele»?"
            secondary.save(update_fields=["prompt"])

    target_skills = {
        "problem-solving": (
            "Rezolvare de probleme",
            "Împărțim sarcina în pași simpli și logici",
        ),
        "digital-safety": (
            "Siguranță digitală",
            "Lucrăm responsabil și protejat în mediul online",
        ),
        "curiosity": (
            "Curiozitate",
            "Învățăm să punem întrebări și să căutăm răspunsuri",
        ),
        "creative-thinking": (
            "Gândire creativă",
            "Găsim mai multe idei pentru aceeași provocare",
        ),
        "communication": (
            "Comunicare clară",
            "Ne exprimăm ideile pe înțelesul tuturor",
        ),
    }

    for slug, (title, description) in target_skills.items():
        skill = Skill.objects.filter(slug=slug).first()
        if not skill:
            continue
        dirty_skill_fields: list[str] = []
        if skill.title != title:
            skill.title = title
            dirty_skill_fields.append("title")
        if skill.description != description:
            skill.description = description
            dirty_skill_fields.append("description")
        if dirty_skill_fields:
            skill.save(update_fields=dirty_skill_fields)


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0022_alter_lessonmedia_audio_duration_seconds_and_more"),
    ]

    operations = [
        migrations.RunPython(update_level1_content, migrations.RunPython.noop),
    ]
