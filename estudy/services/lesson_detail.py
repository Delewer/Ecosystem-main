from __future__ import annotations

import random
import re
from typing import Any, Dict, List

from django.conf import settings

from ..models import Lesson, LessonMedia, LessonProgress
from ..views import _is_competitor_link
from .feature_flags import is_enabled as feature_enabled
from .gamification import get_badge_summary
from .learner_age import (
    filter_lessons_for_track,
    get_registration_profile_age,
    resolve_learning_age_bracket,
)
from .lesson_access import compute_accessibility
from .lesson_guides import get_lesson_learning_guide
from .recommendations import refresh_recommendations

INTRO_LESSON_COUNT = 2
CYRILLIC_RE = re.compile(r"[\u0400-\u04FF]")
PYTHON_TRACK_SUBJECT_NAMES = {
    "coding quest",
    "python",
    "programare in python",
    "programare în python",
}
OLDER_CODE_AGE_BRACKETS = {
    Lesson.AGE_11_13,
    Lesson.AGE_14_16,
    Lesson.AGE_16_PLUS,
}


def _contains_cyrillic(value: str) -> bool:
    return bool(CYRILLIC_RE.search(value or ""))


def _sanitize_display_text(value: str | None, fallback: str = "") -> str:
    text = (value or "").strip()
    if not text or _contains_cyrillic(text):
        return fallback
    return text


def _sanitize_display_list(
    values: list[str] | tuple[str, ...] | None, fallback: list[str] | None = None
) -> list[str]:
    cleaned: list[str] = []
    for value in values or []:
        candidate = _sanitize_display_text(str(value), "")
        if candidate:
            cleaned.append(candidate)
    if cleaned:
        return cleaned
    return list(fallback or [])


def _sanitize_example_cards(
    values: list[dict[str, object]] | tuple[dict[str, object], ...] | None,
    fallback: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for value in values or []:
        if not isinstance(value, dict):
            continue
        title = _sanitize_display_text(str(value.get("title", "")), "")
        code = _sanitize_display_text(str(value.get("code", "")), "")
        note = _sanitize_display_text(str(value.get("note", "")), "")
        if not title and not code and not note:
            continue
        cards.append(
            {
                "title": title or "Exemplu ghidat",
                "code": code or "-",
                "note": note or "Observa rolul fiecarui pas din exemplu.",
            }
        )
    if cards:
        return cards
    return [dict(item) for item in (fallback or []) if isinstance(item, dict)]


def _sanitize_mini_project(value: dict[str, object] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    project = {
        "title": _sanitize_display_text(str(value.get("title", "")), ""),
        "prompt": _sanitize_display_text(str(value.get("prompt", "")), ""),
        "steps": _sanitize_display_list(
            [str(step) for step in value.get("steps", []) if step is not None],
            [],
        ),
        "outcome": _sanitize_display_text(str(value.get("outcome", "")), ""),
    }
    if any(project.values()):
        return project
    return {}


class BlockingLessonRequired(Exception):
    def __init__(self, blocking_slug: str, blocking_title: str | None = None):
        super().__init__(f"Blocking lesson required: {blocking_slug}")
        self.blocking_slug = blocking_slug
        self.blocking_title = blocking_title


def _get_lesson_enrichment(slug: str) -> dict[str, Any]:
    mapping = getattr(settings, "ESTUDY_LESSON_ENRICHMENTS", {})
    if not isinstance(mapping, dict):
        return {}
    enrichment = mapping.get(slug, {})
    return enrichment if isinstance(enrichment, dict) else {}


def _normalize_subject_name(value: str | None) -> str:
    return " ".join((value or "").casefold().split())


def _is_python_track_lesson(lesson: Lesson) -> bool:
    subject_name = _normalize_subject_name(
        getattr(getattr(lesson, "subject", None), "name", "")
    )
    return subject_name in PYTHON_TRACK_SUBJECT_NAMES


def _build_junior_activity_cards(
    lesson: Lesson, practice, lesson_intro_text: str
) -> list[dict[str, str]]:
    practice_hint = _sanitize_display_text(getattr(practice, "instructions", ""), "")
    intro_note = (
        lesson_intro_text or "Priveste modelul, apoi continua cu jocul de mai jos."
    )
    return [
        {
            "title": "Puzzle de ordine",
            "code": "START -> ? -> GOAL",
            "note": "Pune pasii in ordinea corecta ca robotul sa ajunga la final.",
        },
        {
            "title": "Potriveste culorile",
            "code": "ROSU = stop\nVERDE = merge",
            "note": "Leaga fiecare culoare de actiunea potrivita.",
        },
        {
            "title": "Gaseste perechile",
            "code": "robot <-> traseu",
            "note": practice_hint or intro_note,
        },
    ]


def _build_junior_games(
    lesson: Lesson, practice, lesson_intro_text: str
) -> dict[str, Any]:
    practice_hint = _sanitize_display_text(getattr(practice, "instructions", ""), "")
    order_commands = [
        {"token_id": "left-1", "move": "left", "icon": "←", "label": "stanga"},
        {"token_id": "right-1", "move": "right", "icon": "→", "label": "dreapta"},
        {"token_id": "down-1", "move": "down", "icon": "↓", "label": "jos"},
        {"token_id": "right-2", "move": "right", "icon": "→", "label": "dreapta"},
    ]
    memory_cards = [
        {"card_id": "robot-a", "pair": "robot", "label": "Robot", "icon": "R"},
        {"card_id": "path-a", "pair": "path", "label": "Traseu", "icon": "T"},
        {"card_id": "terminal-a", "pair": "terminal", "label": "Terminal", "icon": "X"},
        {"card_id": "robot-b", "pair": "robot", "label": "Robot", "icon": "R"},
        {"card_id": "path-b", "pair": "path", "label": "Traseu", "icon": "T"},
        {"card_id": "terminal-b", "pair": "terminal", "label": "Terminal", "icon": "X"},
    ]
    return {
        "headline": "3 jocuri scurte pentru Robo",
        "summary": "Rezolva toate jocurile ca sa deschizi urmatoarea misiune.",
        "order": {
            "game_id": "order",
            "title": "1. Labirintul lui Robo",
            "prompt": "Alege comenzile corecte si du-l pe Robo la terminal.",
            "hint": "Robo merge doua casute la dreapta, apoi una in jos.",
            "expected": ["right", "right", "down"],
            "commands": order_commands,
            "board": [
                [
                    {"kind": "start", "label": "Start"},
                    {"kind": "path", "label": "Pas 1"},
                    {"kind": "path", "label": "Pas 2"},
                ],
                [
                    {"kind": "wall", "label": "Blocaj"},
                    {"kind": "path", "label": "Pod"},
                    {"kind": "terminal", "label": "Terminal"},
                ],
            ],
        },
        "colors": {
            "game_id": "colors",
            "title": "2. Culori si reguli",
            "prompt": "Atinge o culoare, apoi regula potrivita.",
            "pairs": [
                {
                    "pair_id": "red",
                    "color_name": "Rosu",
                    "color_hex": "#ef4444",
                    "action": "Stop",
                },
                {
                    "pair_id": "yellow",
                    "color_name": "Galben",
                    "color_hex": "#facc15",
                    "action": "Atentie",
                },
                {
                    "pair_id": "green",
                    "color_name": "Verde",
                    "color_hex": "#22c55e",
                    "action": "Merge",
                },
            ],
            "actions": [
                {"pair_id": "yellow", "label": "Atentie"},
                {"pair_id": "green", "label": "Merge"},
                {"pair_id": "red", "label": "Stop"},
            ],
        },
        "memory": {
            "game_id": "memory",
            "title": "3. Carti secrete",
            "prompt": practice_hint
            or lesson_intro_text
            or "Intoarce cartile si gaseste toate perechile.",
            "cards": memory_cards,
        },
    }


def _build_theory_question_prompts(
    lesson: Lesson, quiz_test, lesson_intro_text: str
) -> list[str]:
    prompts = [
        f"Cum ai explica pe scurt lectia '{lesson.title}' unui coleg?",
        lesson_intro_text or "Care este ideea principala pe care trebuie sa o retii?",
    ]
    if quiz_test and getattr(quiz_test, "question", ""):
        prompts.append(f"Cum ai raspunde la intrebarea: {quiz_test.question}")
    else:
        prompts.append("Ce exemplu practic poti da dupa aceasta lectie?")
    return prompts


def _build_mentor_characters(lesson: Lesson) -> list[dict[str, str]]:
    hero_emoji = (lesson.hero_emoji or "").strip() or "ROBO"
    return [
        {
            "name": "Nova",
            "emoji": hero_emoji,
            "role": "Capitanul aventurii",
            "line": "Transformam curiozitatea in pasi mici si distractivi.",
        },
        {
            "name": "Byte",
            "emoji": "BOT",
            "role": "Mecanicul de cod",
            "line": "Iti arat cum fiecare linie de cod face ceva concret.",
        },
        {
            "name": "Pixel",
            "emoji": "FOX",
            "role": "Exploratorul logicii",
            "line": "Daca gresim, invatam rapid si incercam din nou.",
        },
    ]


def _build_code_arena_steps(
    code_exercises, enrichment: dict[str, Any]
) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = []
    for idx, exercise in enumerate(code_exercises[:4], start=1):
        steps.append(
            {
                "title": exercise.title or f"Misiunea {idx}",
                "goal": (
                    exercise.description
                    or "Rezolva provocarea scriind cod Python corect si clar."
                ),
                "xp": str(max(5, int(getattr(exercise, "points", 10) or 10))),
                "badge": f"Dificultate {getattr(exercise, 'difficulty_level', 1)}",
                "target": "#code-exercises",
            }
        )

    if not steps:
        challenges = enrichment.get("code_challenges") or []
        if isinstance(challenges, list):
            for idx, challenge in enumerate(challenges[:4], start=1):
                if not isinstance(challenge, dict):
                    continue
                steps.append(
                    {
                        "title": challenge.get("title") or f"Misiunea {idx}",
                        "goal": challenge.get("prompt")
                        or "Scrie un mic fragment de cod si verifica rezultatul.",
                        "xp": str(challenge.get("xp") or 10),
                        "badge": challenge.get("badge") or "Arena",
                        "target": "#example",
                    }
                )

    if steps:
        return steps

    return [
        {
            "title": "Misiunea 1: Incalzirea",
            "goal": "Declara variabile simple si afiseaza-le cu print().",
            "xp": "10",
            "badge": "Syntax",
            "target": "#example",
        },
        {
            "title": "Misiunea 2: Combo de logica",
            "goal": "Combina text si numere intr-un mesaj clar pentru utilizator.",
            "xp": "15",
            "badge": "Flow",
            "target": "#practice",
        },
        {
            "title": "Misiunea 3: Boss mini-test",
            "goal": "Treci testul final si explica de ce solutia ta functioneaza.",
            "xp": "20",
            "badge": "Mastery",
            "target": "#test",
        },
    ]


def prepare_lesson_detail(user, slug: str) -> dict:
    """Fetch a lesson and prepare the full payload for the view.

    Raises BlockingLessonRequired if a previous required lesson is not completed.
    Returns the payload dict (already containing 'lesson' and 'badges').
    """
    lesson = (
        Lesson.objects.select_related("subject")
        .prefetch_related(
            "materials",
            "tests",
            "code_exercises",
            "objectives",
            "reflection_prompts",
            "skills",
            "media__segments",
            "hints",
            "easter_eggs",
        )
        .filter(slug=slug)
        .first()
    )
    if not lesson:
        raise ValueError("Lesson not found")

    subject_lessons = filter_lessons_for_track(
        lesson.subject.lessons.order_by("date", "id"),
        user=user,
        anchor_lesson=lesson,
    )
    current_index = next(
        (index for index, item in enumerate(subject_lessons) if item.id == lesson.id), 0
    )
    required_lessons = subject_lessons[:current_index]
    completed_in_subject = set(
        LessonProgress.objects.filter(
            user=user, lesson__in=required_lessons, completed=True
        ).values_list("lesson_id", flat=True)
    )
    blocking_lesson = next(
        (item for item in required_lessons if item.id not in completed_in_subject), None
    )
    if blocking_lesson:
        raise BlockingLessonRequired(
            blocking_slug=blocking_lesson.slug, blocking_title=blocking_lesson.title
        )

    # refresh recommendations and compute accessibility
    try:
        recs = refresh_recommendations(user)
    except Exception:
        recs = []

    progress = LessonProgress.objects.filter(user=user, lesson=lesson).first()

    try:
        _, accessible_ids, locked_reasons = compute_accessibility(user)
    except Exception:
        accessible_ids = {lesson.id}
        locked_reasons = {}

    subject_completed_ids = set(
        LessonProgress.objects.filter(
            user=user, lesson__in=subject_lessons, completed=True
        ).values_list("lesson_id", flat=True)
    )

    payload = build_lesson_detail_payload(
        user,
        lesson,
        subject_lessons,
        current_index,
        subject_completed_ids,
        accessible_ids,
        locked_reasons,
        progress,
    )
    payload["lesson"] = lesson
    payload["badges"] = get_badge_summary(user)
    payload["recommendations"] = recs
    return payload


def build_lesson_detail_payload(
    user,
    lesson: Lesson,
    subject_lessons: List[Lesson],
    current_index: int,
    completed_in_subject: set,
    accessible_ids: set,
    locked_reasons: dict,
    progress: LessonProgress | None,
) -> Dict:
    """Build contextual payload for lesson_detail view.

    Returns keys used by template: tests, quiz_test, quiz_options, recommendations, enrichment,
    badges, practice, prev_lesson, next_lesson, next_locked, subject_sequence, lesson_position,
    subject_total, lesson_voice_text, lesson_materials
    """
    tests = list(lesson.tests.order_by("id"))
    quiz_test = tests[0] if tests else None
    quiz_options = []
    if quiz_test:
        quiz_options = [quiz_test.correct_answer, *quiz_test.wrong_answers]
        random.shuffle(quiz_options)

    # recommendations fetched in view/service caller (keep here optional)
    recommendations = []

    enrichment = _get_lesson_enrichment(lesson.slug)
    learning_guide = get_lesson_learning_guide(lesson.slug)

    practice = getattr(lesson, "practice", None)
    code_exercises = list(lesson.code_exercises.order_by("order", "id"))
    is_intro_lesson = (current_index + 1) <= INTRO_LESSON_COUNT
    is_python_track = _is_python_track_lesson(lesson)
    learner_age = get_registration_profile_age(user)
    effective_age_bracket = resolve_learning_age_bracket(
        user, fallback=lesson.age_bracket
    )
    is_junior_track = effective_age_bracket == Lesson.AGE_8_10
    is_older_track = effective_age_bracket in OLDER_CODE_AGE_BRACKETS
    age_mode_label = "8-10 ani" if is_junior_track else "11+ ani"
    age_mode_source = "profile" if learner_age is not None else "lesson"
    mentor_characters = _build_mentor_characters(lesson)
    code_arena_steps = _build_code_arena_steps(code_exercises, enrichment)
    lesson_intro_text = _sanitize_display_text(lesson.theory_intro, "")
    if not lesson_intro_text:
        lesson_intro_text = _sanitize_display_text(lesson.excerpt, "")
    if not lesson_intro_text:
        lesson_intro_text = (
            "Descopera cum poti folosi variabilele pentru programe clare si utile."
        )
    default_example_cards = [
        {
            "title": "Definim o variabila",
            "code": 'nume = "Ana"',
            "note": "Atribui un nume unei valori ca sa o poti refolosi.",
        },
        {
            "title": "Afisam rezultatul",
            "code": 'print(f"Salut, {nume}!")',
            "note": "Folosesti valoarea stocata exact unde ai nevoie.",
        },
        {
            "title": "Actualizam rapid",
            "code": "scor = scor + 1",
            "note": "Schimbi valoarea fara sa rescrii tot programul.",
        },
    ]
    lesson_examples_text = _sanitize_display_text(
        str(learning_guide.get("examples_text", "")),
        "",
    )
    if not lesson_examples_text:
        lesson_examples_text = _sanitize_display_text(
            getattr(lesson, "explainer", ""),
            "",
        )
    if not lesson_examples_text:
        lesson_examples_text = (
            "Recapitulare rapida in trei idei: definesti o variabila, o afisezi, "
            "apoi o actualizezi."
        )
    lesson_story_anchor = _sanitize_display_text(lesson.story_anchor, "")
    lesson_skill_titles = _sanitize_display_list(
        [skill.title for skill in lesson.skills.all()],
        ["Rezolvare de probleme", "Siguranta digitala"],
    )
    lesson_track_items = _sanitize_display_list(
        [str(track) for track in lesson.content_tracks],
        ["Traseu de baza", "Bonus pentru exploratori"],
    )
    lesson_theory_points = _sanitize_display_list(
        [str(point) for point in lesson.theory_points()],
        [],
    )
    lesson_content_text = _sanitize_display_text(
        lesson.content,
        (
            "O variabila pastreaza o informatie importanta pe care codul tau "
            "o poate folosi si modifica."
        ),
    )
    lesson_example_cards = _sanitize_example_cards(
        learning_guide.get("example_cards"),
        default_example_cards,
    )
    lesson_use_cases = _sanitize_display_list(
        learning_guide.get("use_cases"),
        [],
    )
    lesson_vocabulary = _sanitize_display_list(
        learning_guide.get("vocabulary"),
        [],
    )
    lesson_common_mistakes = _sanitize_display_list(
        learning_guide.get("common_mistakes"),
        [],
    )
    lesson_mini_project = _sanitize_mini_project(
        learning_guide.get("mini_project"),
    )
    lesson_fun_fact = _sanitize_display_text(lesson.fun_fact, "")
    guided_code_snippet = _sanitize_display_text(
        str(learning_guide.get("guided_code", "")),
        "",
    )
    if not guided_code_snippet:
        code_challenges = enrichment.get("code_challenges") or []
        if isinstance(code_challenges, list) and code_challenges:
            first_challenge = code_challenges[0]
            if isinstance(first_challenge, dict):
                guided_code_snippet = _sanitize_display_text(
                    str(first_challenge.get("solution", "")),
                    "",
                )
    if not guided_code_snippet:
        guided_code_snippet = (
            'nume = "Alex"\n'
            "varsta = 12\n"
            'mesaj = f"Salut, {nume}! Ai {varsta} ani."\n'
            "print(mesaj)"
        )
    practice_context = _sanitize_display_text(
        str(learning_guide.get("practice_context", "")),
        "",
    )
    junior_games = {}

    if is_junior_track:
        if lesson_theory_points:
            lesson_theory_points = lesson_theory_points[:2]
        if lesson_track_items:
            lesson_track_items = lesson_track_items[:1]
        lesson_content_text = lesson_intro_text or lesson_content_text
        if not learning_guide.get("examples_text"):
            lesson_examples_text = (
                "Priveste modelul, observa ordinea si continua cu jocul de potrivire."
            )
        if not learning_guide.get("example_cards"):
            lesson_example_cards = _build_junior_activity_cards(
                lesson, practice, lesson_intro_text
            )
        junior_games = _build_junior_games(lesson, practice, lesson_intro_text)
    elif not is_python_track and not learning_guide.get("example_cards"):
        lesson_examples_text = "Recapituleaza ideea principala, apoi raspunde la intrebarile de verificare."
        lesson_example_cards = [
            {
                "title": "Ideea cheie",
                "code": "Ce trebuie sa retii?",
                "note": lesson_intro_text,
            },
            {
                "title": "Exemplu simplu",
                "code": "Unde vezi asta in viata reala?",
                "note": "Leaga teoria de un exemplu apropiat de experienta ta.",
            },
            {
                "title": "Verificare rapida",
                "code": "Cum explici lectia in 1-2 propozitii?",
                "note": "Pregateste raspunsul pentru mini-testul de la final.",
            },
        ]

    lesson_recap_questions = _sanitize_display_list(
        learning_guide.get("recap_questions"),
        _build_theory_question_prompts(lesson, quiz_test, lesson_intro_text),
    )
    show_legacy_intro_panels = False
    show_legacy_concept_tabs = False

    robot_lab_enabled = feature_enabled("robot_lab_enabled", user=user, default=True)
    show_robot_lab_preview = is_python_track and is_older_track and robot_lab_enabled
    show_full_code_lab = show_robot_lab_preview
    show_robot_lab_cta = show_robot_lab_preview
    show_guided_code_snippet = is_python_track and not is_junior_track
    example_nav_label = (
        "Robot Lab"
        if show_full_code_lab
        else "Puzzle"
        if is_junior_track
        else "Exemplu"
    )
    example_nav_hint = (
        "Editor Python"
        if show_full_code_lab
        else "Potriviri vizuale"
        if is_junior_track
        else "Model clar"
    )
    practice_nav_label = "Jocuri" if is_junior_track else "Practica"
    practice_nav_hint = "Puzzle" if is_junior_track else "Exercitii"
    concept_examples_label = "Exemple vizuale" if is_junior_track else "Exemple"
    example_section_title = (
        "Robot Lab cu Python"
        if show_full_code_lab
        else "Puzzle si potriviri"
        if is_junior_track
        else "Exemplu pas cu pas"
    )
    example_section_description = (
        "Robot Lab apare aici doar pentru 11+ si se controleaza prin cod Python."
        if show_full_code_lab
        else "Pentru 8-10 ani avem activitati vizuale, simple si cu putin text."
        if is_junior_track
        else "Vezi modelul lectiei, apoi treci la exercitiu."
    )
    practice_section_title = "Puzzle si potriviri" if is_junior_track else "Practica"
    practice_section_description = (
        "Piese mari, reguli simple si feedback rapid."
        if is_junior_track
        else "Potrivesti concepte, primesti feedback instant si corectezi rapid."
    )
    base_practice_intro_text = (
        "Trage piesele, gaseste perechile si apasa Verifica."
        if is_junior_track
        else "Aplica teoria in doi pasi: citeste scenariul, apoi potriveste conceptele. Daca te blochezi, apasa pe Tip."
    )
    practice_intro_text = base_practice_intro_text
    practice_briefing_title = "1. Joc rapid" if is_junior_track else "1. Briefing"
    practice_available_label = (
        "Piese disponibile" if is_junior_track else "Elemente disponibile"
    )
    practice_target_label = "Gaseste perechea:" if is_junior_track else "Potriveste cu:"
    practice_placeholder_text = (
        "Pune piesa aici" if is_junior_track else "Trage elementul aici"
    )
    theory_question_prompts = lesson_recap_questions

    prev_lesson = subject_lessons[current_index - 1] if current_index > 0 else None
    next_lesson = (
        subject_lessons[current_index + 1]
        if current_index < len(subject_lessons) - 1
        else None
    )
    next_locked = bool(next_lesson and next_lesson.id not in accessible_ids)

    subject_sequence = []
    for idx, seq_lesson in enumerate(subject_lessons, start=1):
        subject_sequence.append(
            {
                "lesson": seq_lesson,
                "index": idx,
                "completed": seq_lesson.id in completed_in_subject,
                "accessible": seq_lesson.id in accessible_ids,
                "is_current": seq_lesson.id == lesson.id,
                "locked_reason": locked_reasons.get(seq_lesson.id),
            }
        )

    info_snippets = []
    if lesson_intro_text:
        info_snippets.append(lesson_intro_text)
    if lesson_theory_points:
        info_snippets.append("Puncte-cheie: " + "; ".join(lesson_theory_points))
    if enrichment.get("story_steps"):
        story_text = "; ".join(
            step.get("detail", "")
            for step in enrichment["story_steps"]
            if step.get("detail")
        )
        if story_text:
            info_snippets.append(story_text)
    lesson_voice_text = " ".join(part for part in info_snippets if part).strip()

    lesson_materials = [
        m for m in lesson.materials.all() if not _is_competitor_link(m.url)
    ]

    try:
        lesson_media = lesson.media
    except LessonMedia.DoesNotExist:
        lesson_media = None
    media_segments = []
    if lesson_media:
        media_segments = list(lesson_media.segments.order_by("order", "id"))

    lesson_hints = list(lesson.hints.order_by("section", "hint_level", "order"))
    lesson_easter_eggs = list(lesson.easter_eggs.all())
    reflection_prompts = list(lesson.reflection_prompts.order_by("order", "id"))

    return {
        "progress": progress,
        "tests": tests,
        "quiz_test": quiz_test,
        "quiz_options": quiz_options,
        "recommendations": recommendations,
        "enrichment": enrichment,
        "badges": None,  # badges fetched by caller
        "practice": practice,
        "prev_lesson": prev_lesson,
        "next_lesson": next_lesson,
        "next_locked": next_locked,
        "subject_sequence": subject_sequence,
        "lesson_position": current_index + 1,
        "subject_total": len(subject_lessons),
        "lesson_voice_text": lesson_voice_text,
        "lesson_materials": lesson_materials,
        "code_exercises": code_exercises,
        "lesson_media": lesson_media,
        "media_segments": media_segments,
        "is_intro_lesson": is_intro_lesson,
        "is_python_track": is_python_track,
        "is_junior_track": is_junior_track,
        "is_older_track": is_older_track,
        "learner_age": learner_age,
        "effective_age_bracket": effective_age_bracket,
        "age_mode_label": age_mode_label,
        "age_mode_source": age_mode_source,
        "mentor_characters": mentor_characters,
        "code_arena_steps": code_arena_steps,
        "lesson_intro_text": lesson_intro_text,
        "lesson_story_anchor": lesson_story_anchor,
        "lesson_skill_titles": lesson_skill_titles,
        "lesson_track_items": lesson_track_items,
        "lesson_theory_points": lesson_theory_points,
        "lesson_content_text": lesson_content_text,
        "lesson_examples_text": lesson_examples_text,
        "lesson_example_cards": lesson_example_cards,
        "lesson_use_cases": lesson_use_cases,
        "lesson_vocabulary": lesson_vocabulary,
        "lesson_common_mistakes": lesson_common_mistakes,
        "lesson_mini_project": lesson_mini_project,
        "lesson_fun_fact": lesson_fun_fact,
        "guided_code_snippet": guided_code_snippet,
        "practice_context": practice_context,
        "lesson_recap_questions": lesson_recap_questions,
        "show_legacy_intro_panels": show_legacy_intro_panels,
        "show_legacy_concept_tabs": show_legacy_concept_tabs,
        "junior_games": junior_games,
        "show_robot_lab_preview": show_robot_lab_preview,
        "show_full_code_lab": show_full_code_lab,
        "show_robot_lab_cta": show_robot_lab_cta,
        "show_guided_code_snippet": show_guided_code_snippet,
        "example_nav_label": example_nav_label,
        "example_nav_hint": example_nav_hint,
        "practice_nav_label": practice_nav_label,
        "practice_nav_hint": practice_nav_hint,
        "concept_examples_label": concept_examples_label,
        "example_section_title": example_section_title,
        "example_section_description": example_section_description,
        "practice_section_title": practice_section_title,
        "practice_section_description": practice_section_description,
        "practice_intro_text": practice_intro_text,
        "practice_briefing_title": practice_briefing_title,
        "practice_available_label": practice_available_label,
        "practice_target_label": practice_target_label,
        "practice_placeholder_text": practice_placeholder_text,
        "theory_question_prompts": theory_question_prompts,
        "lesson_hints": lesson_hints,
        "lesson_easter_eggs": lesson_easter_eggs,
        "reflection_prompts": reflection_prompts,
    }
