from __future__ import annotations

from datetime import timedelta
from typing import Any

from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone

from ..models import (
    Classroom,
    ClassroomMembership,
    CodeExercise,
    LearnerCheckIn,
    Lesson,
    LessonProgress,
    TestAttempt,
)
from .learner_age import (
    filter_lessons_for_user_age,
    get_registration_profile_age,
    resolve_learning_age_bracket,
)
from .lesson_access import compute_accessibility
from .personalized_practice import (
    TASK_CODE_EXERCISE,
    TASK_LESSON_REVIEW,
    TASK_QUIZ_RETRY,
    generate_personalized_practice,
)
from .teacher_early_warning import build_teacher_early_warning_report

AGE_TRACK_JUNIOR = "junior"
AGE_TRACK_OLDER = "older"
DEFAULT_DASHBOARD_RECOMMENDATIONS = 3
DEFAULT_PRACTICE_DAYS = 3
DEFAULT_SUPPORT_LIMIT = 8

TASK_LABELS = {
    TASK_LESSON_REVIEW: "Recapitulare",
    TASK_QUIZ_RETRY: "Intrebari gresite",
    TASK_CODE_EXERCISE: "Exercitiu de cod",
}


def get_age_track(user) -> dict[str, Any]:
    age = get_registration_profile_age(user)
    bracket = resolve_learning_age_bracket(user)
    is_junior = age is not None and age <= 10
    if bracket == Lesson.AGE_8_10:
        is_junior = True
    return {
        "age": age,
        "bracket": bracket,
        "key": AGE_TRACK_JUNIOR if is_junior else AGE_TRACK_OLDER,
        "label": "Junior 8-10" if is_junior else "Code 11+",
        "summary": (
            "Pasi vizuali, jocuri scurte si Robot Lab."
            if is_junior
            else "Cod, proiecte, teste si explicatii dupa greseli."
        ),
    }


def _lesson_url(lesson: Lesson | None) -> str:
    if lesson is None or not lesson.slug:
        return ""
    return reverse("estudy:lesson_detail", kwargs={"slug": lesson.slug})


def _code_exercise_url(exercise_id: int | None) -> str:
    if not exercise_id:
        return ""
    return reverse("estudy:code_exercise", kwargs={"pk": exercise_id})


def _profile_goal(user) -> str:
    profile = getattr(user, "userprofile", None)
    return getattr(profile, "learning_goal", "") if profile else ""


def _favorite_subject_id(user) -> int | None:
    profile = getattr(user, "userprofile", None)
    subject = getattr(profile, "favorite_subject", None) if profile else None
    return getattr(subject, "id", None)


def _score_lesson(user, lesson: Lesson, accessible_ids: set[int]) -> int:
    score = 0
    if lesson.id in accessible_ids:
        score += 30

    preferred_bracket = resolve_learning_age_bracket(user)
    if preferred_bracket and lesson.age_bracket == preferred_bracket:
        score += 12

    favorite_subject_id = _favorite_subject_id(user)
    if favorite_subject_id and lesson.subject_id == favorite_subject_id:
        score += 10

    goal = _profile_goal(user)
    subject_name = (getattr(lesson.subject, "name", "") or "").lower()
    if goal in {"skills", "career"} and any(
        token in subject_name for token in ("python", "coding", "web")
    ):
        score += 6
    if goal == "fun" and lesson.lesson_type in {
        Lesson.LESSON_TYPE_INTERACTIVE,
        Lesson.LESSON_TYPE_PROJECT,
        Lesson.LESSON_TYPE_QUIZ,
    }:
        score += 6
    if goal == "grades" and lesson.tests.exists():
        score += 5

    return score


def _next_lesson_reason(user, lesson: Lesson | None) -> str:
    if lesson is None:
        return "Ai terminat lectiile disponibile. Alege o provocare noua din catalog."
    track = get_age_track(user)
    goal = _profile_goal(user)
    if goal == "grades":
        return "Alegem un pas cu test, bun pentru consolidare scolara."
    if goal == "career":
        return "Alegem un pas care construieste abilitati utile pentru proiecte reale."
    if goal == "fun":
        return "Alegem un pas scurt si interactiv, potrivit pentru ritmul tau."
    return f"Urmatorul pas disponibil pentru traseul {track['label']}."


def _pick_next_lesson(user) -> Lesson | None:
    completed_ids = set(
        LessonProgress.objects.filter(user=user, completed=True).values_list(
            "lesson_id", flat=True
        )
    )
    completed_ids_from_access, accessible_ids, _locked = compute_accessibility(user)
    accessible_ids = set(accessible_ids).union(completed_ids_from_access)

    lessons = list(
        Lesson.objects.select_related("subject")
        .exclude(id__in=completed_ids)
        .order_by("date", "id")
    )
    if not lessons:
        return None

    age_filtered = filter_lessons_for_user_age(lessons, user)
    candidates = [lesson for lesson in age_filtered if lesson.id in accessible_ids]
    if not candidates:
        candidates = age_filtered or lessons

    candidates.sort(
        key=lambda lesson: (
            -_score_lesson(user, lesson, accessible_ids),
            lesson.date,
            lesson.id,
        )
    )
    return candidates[0] if candidates else None


def _build_recent_mistakes(user, limit: int = 3) -> list[dict[str, Any]]:
    attempts = (
        TestAttempt.objects.filter(user=user, is_correct=False)
        .select_related("test__lesson")
        .order_by("-created_at")
    )
    mistakes: list[dict[str, Any]] = []
    seen_tests: set[int] = set()
    for attempt in attempts:
        if attempt.test_id in seen_tests:
            continue
        seen_tests.add(attempt.test_id)
        lesson = attempt.test.lesson
        mistakes.append(
            {
                "lesson": lesson,
                "test": attempt.test,
                "selected_answer": attempt.selected_answer,
                "correct_answer": attempt.test.correct_answer,
                "action_url": _lesson_url(lesson),
                "created_at": attempt.created_at,
            }
        )
        if len(mistakes) >= limit:
            break
    return mistakes


def _pick_review_lesson(
    user, mistakes: list[dict[str, Any]]
) -> tuple[Lesson | None, str]:
    help_checkin = (
        LearnerCheckIn.objects.filter(user=user)
        .filter(
            Q(help_requested=True) | Q(difficulty=LearnerCheckIn.DIFFICULTY_TOO_HARD)
        )
        .select_related("lesson")
        .order_by("-updated_at")
        .first()
    )
    if help_checkin:
        return (
            help_checkin.lesson,
            "Ai cerut ajutor aici, asa ca reluam ideea pe pasi mici.",
        )
    if mistakes:
        return (
            mistakes[0]["lesson"],
            "Ai avut o eroare recenta aici. Recapitularea te ajuta sa fixezi regula.",
        )
    completed = (
        LessonProgress.objects.filter(user=user, completed=True)
        .select_related("lesson")
        .order_by("-completed_at", "-updated_at")
        .first()
    )
    if completed:
        return completed.lesson, "O recapitulare scurta pastreaza ideea proaspata."
    return None, "Nu ai inca lectii de repetat. Incepem cu un pas nou."


def _normalize_practice_tasks(user) -> list[dict[str, Any]]:
    result = generate_personalized_practice(
        user, days=DEFAULT_PRACTICE_DAYS, tasks_per_day=3
    )
    if not result.success:
        return []
    first_day = next(iter(result.data.get("days", [])), None)
    if not first_day:
        return []

    lesson_ids = [task.get("lesson_id") for task in first_day.get("tasks", [])]
    lessons = {
        lesson.id: lesson
        for lesson in Lesson.objects.filter(id__in=lesson_ids).select_related("subject")
    }

    tasks: list[dict[str, Any]] = []
    for task in first_day.get("tasks", []):
        lesson = lessons.get(task.get("lesson_id"))
        item_id = next(iter(task.get("items", []) or []), None)
        task_type = task.get("task_type")
        action_url = _lesson_url(lesson)
        if task_type == TASK_CODE_EXERCISE and item_id:
            if CodeExercise.objects.filter(id=item_id).exists():
                action_url = _code_exercise_url(item_id)
        tasks.append(
            {
                "task_type": task_type,
                "label": TASK_LABELS.get(task_type, "Practica"),
                "lesson": lesson,
                "lesson_title": task.get("lesson_title"),
                "reason": task.get("reason"),
                "estimated_time": task.get("estimated_time") or 10,
                "action_url": action_url,
            }
        )
    return tasks


def _dashboard_recommendations(today_plan: dict[str, Any]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for item in (
        today_plan.get("next_lesson"),
        today_plan.get("review_task"),
        *(today_plan.get("practice_tasks") or []),
    ):
        if not item:
            continue
        lesson = item.get("lesson")
        if lesson is None or any(
            rec["lesson"].id == lesson.id for rec in recommendations
        ):
            continue
        recommendations.append(
            {
                "lesson": lesson,
                "reason": item.get("reason") or "Bun de parcurs in continuare.",
                "action_url": item.get("action_url") or _lesson_url(lesson),
            }
        )
        if len(recommendations) >= DEFAULT_DASHBOARD_RECOMMENDATIONS:
            break
    return recommendations


def build_today_learning_plan(user) -> dict[str, Any]:
    recent_mistakes = _build_recent_mistakes(user)
    next_lesson = _pick_next_lesson(user)
    review_lesson, review_reason = _pick_review_lesson(user, recent_mistakes)
    practice_tasks = _normalize_practice_tasks(user)

    next_task = {
        "lesson": next_lesson,
        "reason": _next_lesson_reason(user, next_lesson),
        "estimated_time": (
            getattr(next_lesson, "duration_minutes", 15) if next_lesson else 0
        ),
        "action_url": _lesson_url(next_lesson),
    }
    review_task = (
        {
            "lesson": review_lesson,
            "reason": review_reason,
            "estimated_time": min(getattr(review_lesson, "duration_minutes", 10), 15),
            "action_url": _lesson_url(review_lesson),
        }
        if review_lesson
        else None
    )

    total_minutes = int(next_task["estimated_time"] or 0)
    if review_task:
        total_minutes += int(review_task["estimated_time"] or 0)
    total_minutes += sum(
        int(task.get("estimated_time") or 0) for task in practice_tasks[:1]
    )

    plan = {
        "age_track": get_age_track(user),
        "next_lesson": next_task,
        "review_task": review_task,
        "practice_tasks": practice_tasks,
        "recent_mistakes": recent_mistakes,
        "estimated_minutes": total_minutes,
        "recommendations": [],
    }
    plan["recommendations"] = _dashboard_recommendations(plan)
    return plan


def record_learner_checkin(
    user,
    lesson: Lesson,
    *,
    mood: str,
    difficulty: str,
    note: str = "",
) -> LearnerCheckIn:
    valid_moods = {choice[0] for choice in LearnerCheckIn.MOOD_CHOICES}
    valid_difficulties = {choice[0] for choice in LearnerCheckIn.DIFFICULTY_CHOICES}
    normalized_mood = mood if mood in valid_moods else LearnerCheckIn.MOOD_UNDERSTOOD
    normalized_difficulty = (
        difficulty
        if difficulty in valid_difficulties
        else LearnerCheckIn.DIFFICULTY_JUST_RIGHT
    )
    help_requested = (
        normalized_mood == LearnerCheckIn.MOOD_NEEDS_HELP
        or normalized_difficulty == LearnerCheckIn.DIFFICULTY_TOO_HARD
    )
    checkin, _created = LearnerCheckIn.objects.update_or_create(
        user=user,
        lesson=lesson,
        defaults={
            "mood": normalized_mood,
            "difficulty": normalized_difficulty,
            "help_requested": help_requested,
            "note": (note or "").strip()[:1000],
        },
    )
    return checkin


def _display_name(user) -> str:
    profile = getattr(user, "userprofile", None)
    if profile and hasattr(profile, "display_or_username"):
        return profile.display_or_username()
    return user.get_short_name() or user.username


def build_teacher_support_snapshot(
    teacher, *, limit: int = DEFAULT_SUPPORT_LIMIT
) -> dict[str, Any]:
    classrooms = list(Classroom.objects.filter(owner=teacher, archived=False))
    if not classrooms:
        return {"students_needing_help": [], "weak_topics": [], "checkins": []}

    memberships = (
        ClassroomMembership.objects.filter(
            classroom__in=classrooms,
            role=ClassroomMembership.ROLE_STUDENT,
            approved=True,
        )
        .select_related("classroom", "user", "user__userprofile")
        .order_by("classroom__name", "user__username")
    )
    student_ids = {membership.user_id for membership in memberships}
    if not student_ids:
        return {"students_needing_help": [], "weak_topics": [], "checkins": []}

    support_by_student: dict[int, dict[str, Any]] = {}

    def ensure_student(user) -> dict[str, Any]:
        entry = support_by_student.setdefault(
            user.id,
            {
                "student": user,
                "display_name": _display_name(user),
                "risk_band": "low",
                "risk_score": 0,
                "reasons": set(),
                "classrooms": set(),
                "help_requested": False,
                "latest_checkin": None,
                "recommendation": "Planifica o verificare scurta la urmatoarea ora.",
            },
        )
        return entry

    membership_by_student = {}
    for membership in memberships:
        membership_by_student.setdefault(membership.user_id, membership)
        ensure_student(membership.user)["classrooms"].add(membership.classroom.name)

    for classroom in classrooms:
        report = build_teacher_early_warning_report(classroom, max_alerts=limit)
        if not report.success:
            continue
        for alert in report.data["alerts"]:
            membership = membership_by_student.get(alert.student_id)
            if not membership:
                continue
            entry = ensure_student(membership.user)
            entry["risk_band"] = alert.risk_band
            entry["risk_score"] = alert.risk_score
            entry["reasons"].update(alert.reasons)

    recent_checkins = list(
        LearnerCheckIn.objects.filter(user_id__in=student_ids, help_requested=True)
        .select_related("user", "user__userprofile", "lesson")
        .order_by("-updated_at")[:limit]
    )
    for checkin in recent_checkins:
        entry = ensure_student(checkin.user)
        entry["help_requested"] = True
        entry["latest_checkin"] = checkin
        entry["reasons"].add("asked_for_help")
        if checkin.difficulty == LearnerCheckIn.DIFFICULTY_TOO_HARD:
            entry["reasons"].add("lesson_too_hard")
        entry[
            "recommendation"
        ] = "Revizuieste lectia impreuna si ofera un exemplu ghidat."

    band_rank = {"high": 0, "medium": 1, "low": 2}
    students_needing_help = []
    for entry in support_by_student.values():
        if (
            not entry["help_requested"]
            and entry["risk_band"] == "low"
            and not entry["reasons"]
        ):
            continue
        entry["reasons"] = sorted(entry["reasons"])
        entry["classrooms"] = sorted(entry["classrooms"])
        students_needing_help.append(entry)

    students_needing_help.sort(
        key=lambda item: (
            not item["help_requested"],
            band_rank.get(item["risk_band"], 3),
            -float(item["risk_score"] or 0),
            item["display_name"].lower(),
        )
    )

    weak_topics = list(
        TestAttempt.objects.filter(user_id__in=student_ids, is_correct=False)
        .values("test__lesson_id", "test__lesson__title")
        .annotate(mistakes=Count("id"))
        .order_by("-mistakes", "test__lesson__title")[:5]
    )

    return {
        "students_needing_help": students_needing_help[:limit],
        "weak_topics": weak_topics,
        "checkins": recent_checkins,
    }


def build_parent_weekly_summary(children) -> list[dict[str, Any]]:
    week_ago = timezone.now() - timedelta(days=7)
    summaries: list[dict[str, Any]] = []
    for child in children:
        completed = list(
            LessonProgress.objects.filter(
                user=child,
                completed=True,
                completed_at__gte=week_ago,
            )
            .select_related("lesson")
            .order_by("-completed_at")[:5]
        )
        wrong_attempts = TestAttempt.objects.filter(
            user=child, is_correct=False, created_at__gte=week_ago
        ).select_related("test__lesson")
        help_checkins = list(
            LearnerCheckIn.objects.filter(
                user=child, help_requested=True, updated_at__gte=week_ago
            )
            .select_related("lesson")
            .order_by("-updated_at")[:3]
        )
        weak_lesson = (
            wrong_attempts.values("test__lesson__title")
            .annotate(mistakes=Count("id"))
            .order_by("-mistakes")
            .first()
        )
        if help_checkins:
            discussion = (
                f"Intreaba ce pas a fost greu in lectia "
                f"'{help_checkins[0].lesson.title}' si lucrati 10 minute impreuna."
            )
        elif weak_lesson:
            discussion = (
                f"Recapitulati pe scurt tema '{weak_lesson['test__lesson__title']}'."
            )
        elif completed:
            discussion = (
                f"Cere-i sa iti explice cu propriile cuvinte lectia "
                f"'{completed[0].lesson.title}'."
            )
        else:
            discussion = "Stabiliti o sesiune scurta de 15 minute pentru urmatorul pas."

        summaries.append(
            {
                "child": child,
                "completed_count": len(completed),
                "completed_lessons": completed,
                "mistake_count": wrong_attempts.count(),
                "help_checkins": help_checkins,
                "discussion_prompt": discussion,
            }
        )
    return summaries
