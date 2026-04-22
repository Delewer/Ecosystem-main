from __future__ import annotations

from django.conf import settings
from django.utils import timezone

from ..models import AIHintRequest, EventLog
from .ai_context import build_lesson_clues
from .ai_cost_tracking import record_ai_cost
from .ai_hallucination_guard import guard_hint_response
from .audit_logger import log_event

DEFAULT_AI_LIMIT_PER_HOUR = 20


def _keyword_hint(question: str) -> str | None:
    q = question.lower()
    keyword_tips = [
        (
            ("variabil", "variabile"),
            (
                "Imaginează-ți variabilele ca pe niște cutii cu etichete. "
                "Pune o valoare clară în cutie și folosește exact același nume "
                "când ai nevoie de ea."
            ),
        ),
        (
            ("loop", "bucl", "repet"),
            (
                "Stabilește ce se schimbă la fiecare iterație și ce condiție oprește bucla. "
                "Scrie acea condiție înainte de cod."
            ),
        ),
        (
            ("condit", "if", "else"),
            (
                "Formulează propoziția „Dacă ... atunci ... altfel ...” în română "
                "și abia apoi trad-o în if/else."
            ),
        ),
        (
            ("lista", "array"),
            (
                "Gândește-te la liste ca la rafturi numerotate. Indicii pornesc de la 0, "
                "deci elementul al treilea are index 2."
            ),
        ),
    ]
    for keywords, tip in keyword_tips:
        if any(word in q for word in keywords):
            return tip
    return None


def _build_answer(question: str, lesson) -> str:
    user_question = question.strip() or "Am nevoie de un indiciu."
    keyword_tip = _keyword_hint(user_question)
    lesson_clues = build_lesson_clues(lesson)

    main_tip = keyword_tip or (
        lesson_clues[0]
        if lesson_clues
        else "Reia exemplul din secțiunea Concept și notează pașii pe scurt."
    )

    extra_tip = (
        lesson_clues[1]
        if len(lesson_clues) > 1
        else "Testează varianta ta în mini-editorul din Example și observă output-ul."
    )

    next_step = "Intră în Practice și vezi dacă poți aplica imediat indiciul."
    if lesson and getattr(lesson, "practice", None):
        next_step = (
            "În Practice, pornește de la hint-ul disponibil și potrivește elementele "
            "ținând cont de cuvintele cheie."
        )
    if lesson and lesson.tests.exists():
        next_step += " Apoi revino la Test pentru a fixa ideea."

    lines = [
        f"Întrebare primită: „{user_question}”.",
        f"1) Hint rapid: {main_tip}",
        f"2) Mai încearcă: {extra_tip}",
        f"Pas următor: {next_step}",
    ]
    return "\n".join(lines)


def generate_hint(user, question: str, *, lesson=None) -> AIHintRequest:
    # simple rate limiting per user per hour
    limit = getattr(
        settings, "ESTUDY_AI_HINT_LIMIT_PER_HOUR", DEFAULT_AI_LIMIT_PER_HOUR
    )
    recent_count = AIHintRequest.objects.filter(
        user=user, created_at__gte=timezone.now() - timezone.timedelta(hours=1)
    ).count()
    if recent_count >= limit:
        raise ValueError("AI hint limit reached. Try again later.")

    raw_answer = _build_answer(question or "", lesson)
    guard_result = guard_hint_response(
        question=question or "",
        answer=raw_answer,
        lesson=lesson,
    )
    answer = guard_result.data.get("answer", raw_answer)
    request = AIHintRequest.objects.create(
        user=user,
        lesson=lesson,
        question=question,
        response=answer,
        resolved_at=timezone.now(),
    )
    guard_signals = guard_result.data.get("signals", [])
    log_event(
        EventLog.EVENT_TEST_SUBMIT,
        user=user,
        metadata={
            "lesson_id": lesson.id if lesson else None,
            "hint_length": len(answer),
            "question": question[:120],
            "guard_signals": guard_signals,
            "guard_modified": bool(guard_result.data.get("modified")),
        },
    )
    record_ai_cost(request)
    return request
