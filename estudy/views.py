from __future__ import annotations

import json
from urllib.parse import urlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import NotificationPreferenceForm, ProfileForm
from .models import (
    EventLog,
    Lesson,
    LessonComment,
    LessonProgress,
    LessonRating,
    Notification,
    NotificationPreference,
    Subject,
    Test,
    TestAttempt,
    UserProfile,
)
from .services.ai import generate_hint
from .services.analytics import LessonAnalyticsService
from .services.audit_logger import log_event
from .services.code_runner import CodeRunner
from .services.gamification import (
    build_overall_progress,
    get_badge_summary,
    get_leaderboard_snapshot,
    get_mission_context,
    record_lesson_completion,
)
from .services.learner_age import (
    filter_lessons_for_user_age,
    get_registration_profile_age,
    lesson_track_key,
)
from .services.notifications import notify_feedback, send_notification
from .services.permissions import (
    ACTION_ANALYTICS_VIEW,
    ACTION_CLASSROOM_MANAGE,
    ACTION_DASHBOARD_ADMIN,
    ACTION_DASHBOARD_PARENT,
    ACTION_DASHBOARD_TEACHER,
    ACTION_MODERATE_COMMENTS,
    action_required,
)

try:
    from .forms import (
        ClassAssignmentForm,
        ClassroomForm,
        ProjectSubmissionForm,
        ReplyForm,
        ThreadForm,
    )
except ImportError:
    ClassAssignmentForm = (
        ClassroomForm
    ) = ProjectSubmissionForm = ReplyForm = ThreadForm = None

try:
    from .models import (
        ClassAssignment,
        Classroom,
        ClassroomMembership,
        CommunityReply,
        CommunityThread,
        ParentChildLink,
        Project,
        ProjectSubmission,
    )
except ImportError:
    ClassAssignment = (
        Classroom
    ) = (
        ClassroomMembership
    ) = (
        CommunityReply
    ) = CommunityThread = ParentChildLink = Project = ProjectSubmission = None

# recommendations are used inside services, not directly in views

ROLE_STUDENT = UserProfile.ROLE_STUDENT
ROLE_TEACHER = UserProfile.ROLE_PROFESSOR
ROLE_ADMIN = UserProfile.ROLE_ADMIN
ROLE_PARENT = UserProfile.ROLE_PARENT

MODULE_LESSON_ALIASES = {}
DIGITAL_LITERACY_MODULE_SLUG = "modul-1-alfabetizare-digitala"
PYTHON_TRACK_SUBJECT_NAMES = (
    "Coding Quest",
    "Programare in Python",
    "Programare în Python",
    "Python",
)
LEADERBOARD_LIMIT = 20


def _robot_lab_enabled(user) -> bool:
    from .services.feature_flags import is_enabled as feature_enabled

    return feature_enabled("robot_lab_enabled", user=user, default=True)


def _robot_lab_tile_kind(symbol: str) -> str:
    mapping = {
        "#": "wall",
        ".": "floor",
        "S": "start",
        "G": "goal",
        "T": "terminal",
        "B": "battery",
        "K": "key",
        "D": "door",
        "H": "hazard",
    }
    return mapping.get(symbol, "floor")


def _pick_robot_lab_summary_level(
    levels: list[dict], preferred_track: str | None = None
) -> dict | None:
    entries = [item for item in levels or [] if isinstance(item, dict)]
    if not entries:
        return None

    def _select(*, track: str | None = None, require_incomplete: bool = False):
        for item in entries:
            if not item.get("unlocked"):
                continue
            if require_incomplete and item.get("completed"):
                continue
            if track and str(item.get("mode") or "").strip().lower() != track:
                continue
            return item
        return None

    if preferred_track:
        return _select(track=preferred_track, require_incomplete=True) or _select(
            track=preferred_track
        )
    return _select(require_incomplete=True) or _select()


def _build_robot_lab_level_json(level: dict) -> str:
    return json.dumps(
        {
            "id": level.get("id"),
            "title": level.get("title"),
            "goal": level.get("goal") or {},
            "goal_text": level.get("goal_text") or "",
            "grid": level.get("grid") or [],
            "legend": level.get("legend") or {},
            "starter_code": level.get("starter_code") or "",
            "max_steps": int(level.get("max_steps") or 200),
            "xp_reward": int(level.get("xp_reward") or 0),
            "allowed_api": level.get("allowed_api") or [],
            "concepts": level.get("concepts") or [],
            "mode": level.get("mode") or "code",
            "mode_label": level.get("mode_label") or "Mod Cod",
            "ui_stage": level.get("ui_stage") or "code",
            "ui_stage_label": level.get("ui_stage_label") or "Cod complet",
            "ui_stage_description": level.get("ui_stage_description") or "",
            "recommended_age": level.get("recommended_age") or "11+",
            "start_dir": level.get("start_dir") or "E",
        }
    )


def _build_robot_lab_lesson_preview(
    user, *, prefer_code_mode: bool = False
) -> dict | None:
    try:
        from .services.robot_lab_levels import load_level, ordered_level_ids
    except Exception:
        return None

    level_ids = ordered_level_ids()
    if not level_ids:
        return None

    age_recommendation = _build_robot_lab_age_recommendation(user)
    preferred_track = "code" if prefer_code_mode else age_recommendation.get("track")
    selected_level_id = "W1-L03" if "W1-L03" in level_ids else level_ids[0]
    play_url = None
    hub_url = None
    selected_is_unlocked = False
    summary_data = {
        "completed_levels": 0,
        "unlocked_levels": 1,
        "total_levels": len(level_ids),
        "progress_percent": 0,
    }

    if user.is_authenticated and _robot_lab_enabled(user):
        try:
            from .services.robot_lab_progress import build_robot_lab_progress_summary

            summary = build_robot_lab_progress_summary(user)
            suggested = _pick_robot_lab_summary_level(
                summary.get("levels", []),
                preferred_track=preferred_track,
            )
            if suggested and suggested.get("id"):
                selected_level_id = str(suggested["id"])
                selected_is_unlocked = bool(suggested.get("unlocked"))
            summary_data = {
                "completed_levels": int(summary.get("completed_levels") or 0),
                "unlocked_levels": int(summary.get("unlocked_levels") or 0),
                "total_levels": int(summary.get("total_levels") or len(level_ids)),
                "progress_percent": int(summary.get("progress_percent") or 0),
            }
        except Exception:
            play_url = None
            hub_url = None

    try:
        level = load_level(selected_level_id)
    except Exception:
        return None

    legend = level.get("legend") or {}
    used_symbols = set()
    grid_rows = []
    raw_grid = level.get("grid") or []
    cols = max((len(str(row)) for row in raw_grid), default=0)
    for row in raw_grid:
        cells = []
        for symbol in str(row):
            used_symbols.add(symbol)
            cells.append(
                {
                    "value": symbol,
                    "kind": _robot_lab_tile_kind(symbol),
                    "label": legend.get(symbol) or _robot_lab_tile_kind(symbol),
                    "overlay": "" if symbol in {".", "#"} else symbol,
                }
            )
        grid_rows.append(cells)

    legend_order = ["S", "G", "T", "B", "K", "D", "H", "#", "."]
    legend_items = []
    for symbol in legend_order:
        if symbol not in used_symbols:
            continue
        legend_items.append(
            {
                "symbol": symbol,
                "kind": _robot_lab_tile_kind(symbol),
                "label": legend.get(symbol) or _robot_lab_tile_kind(symbol),
            }
        )

    if user.is_authenticated and _robot_lab_enabled(user) and selected_is_unlocked:
        play_url = reverse("estudy:robot_lab_game", args=[selected_level_id])
        hub_url = reverse("estudy:robot_lab_world_map")

    level_json = _build_robot_lab_level_json(level)
    level_age_recommendation = _build_robot_lab_age_recommendation(
        user, level_mode=str(level.get("mode") or "code")
    )

    return {
        "id": str(level.get("id") or selected_level_id),
        "title": level.get("title") or "Robot Lab",
        "description": level.get("description")
        or "Scrie Python si ghideaza robotul pe harta.",
        "goal_text": level.get("goal_text") or "Completeaza misiunea robotului.",
        "starter_code": level.get("starter_code") or "move()",
        "concepts": list(level.get("concepts") or []),
        "concept_labels": list(
            level.get("concept_labels") or level.get("concepts") or []
        ),
        "allowed_api": list(level.get("allowed_api") or []),
        "xp_reward": int(level.get("xp_reward") or 0),
        "max_steps": int(level.get("max_steps") or 0),
        "mode": level.get("mode") or "code",
        "mode_label": level.get("mode_label") or "Mod Cod",
        "ui_stage": level.get("ui_stage") or "code",
        "ui_stage_label": level.get("ui_stage_label") or "Cod complet",
        "ui_stage_description": level.get("ui_stage_description")
        or "Scrie singur programul si ruleaza-l.",
        "recommended_age": level.get("recommended_age") or "11+",
        "start_dir": level.get("start_dir") or "E",
        "goal": level.get("goal") or {},
        "legend": level.get("legend") or {},
        "grid": raw_grid,
        "grid_rows": grid_rows,
        "grid_cols": cols,
        "legend_items": legend_items,
        "play_url": play_url,
        "hub_url": hub_url,
        "is_enabled": bool(play_url),
        "level_json": level_json,
        "age_recommendation": level_age_recommendation,
        "summary": summary_data,
        "flow_steps": ["Scrie", "Ruleaza", "Observa", "Reflecta", "Imbunatateste"],
    }


def _build_robot_lab_age_recommendation(
    user, *, level_mode: str | None = None
) -> dict[str, object]:
    learner_age = get_registration_profile_age(user)
    mode_labels = {
        "junior": "Mod Junior",
        "code": "Mod Cod",
    }
    recommendation = {
        "age": learner_age,
        "has_profile_age": learner_age is not None,
        "track": None,
        "track_label": "",
        "description": "",
        "mismatch": False,
        "mismatch_note": "",
    }
    if learner_age is None:
        return recommendation

    if learner_age <= 10:
        recommendation["track"] = "junior"
        recommendation["track_label"] = "Mod Junior"
        recommendation[
            "description"
        ] = "Pentru 8-10 ani recomandam butoane mari, trasee vizuale si foarte putin text."
    else:
        recommendation["track"] = "code"
        recommendation["track_label"] = "Mod Cod"
        recommendation[
            "description"
        ] = "Pentru 11+ recomandam editor Python, consola si feedback de depanare."

    current_mode = str(level_mode or "").strip().lower()
    if current_mode and current_mode != recommendation["track"]:
        recommendation["mismatch"] = True
        recommendation["mismatch_note"] = (
            f"Nivelul acesta foloseste {mode_labels.get(current_mode, current_mode)}. "
            f"Pentru profilul tau recomandarea principala este {recommendation['track_label']}."
        )
    return recommendation


def with_progress(context: dict, user) -> dict:
    if user.is_authenticated:
        context.setdefault("global_progress", build_overall_progress(user))
    else:
        context.setdefault(
            "global_progress", {"percent": 0, "completed": 0, "total": 0}
        )
    return context


def get_profile(user: User) -> UserProfile:
    try:
        return user.userprofile
    except UserProfile.DoesNotExist as exc:
        raise Http404("Profil lipsa") from exc


def _get_competitor_domains() -> set[str]:
    raw = getattr(settings, "ESTUDY_COMPETITOR_DOMAINS", None)
    if not raw:
        return set()
    try:
        # accept list/tuple/CSV string
        if isinstance(raw, (list, tuple, set)):
            items = raw
        else:
            items = [p.strip() for p in str(raw).split(",") if p.strip()]
        return set(str(d).lower().lstrip(".") for d in items)
    except Exception:
        return set()


def _is_competitor_link(url: str) -> bool:
    """Return True when the provided URL belongs to a known competitor domain.

    Domains are read from Django setting `ESTUDY_COMPETITOR_DOMAINS` and
    compared against the URL hostname suffix.
    """
    if not url:
        return False
    try:
        netloc = urlparse(url).netloc.lower()
    except Exception:
        return False
    domains = _get_competitor_domains()
    if not domains:
        return False
    return any(netloc == domain or netloc.endswith("." + domain) for domain in domains)


def _prefetched_subjects():
    from .services.lesson_access import prefetched_subjects

    return prefetched_subjects()


def _compute_accessibility(user, subjects=None):
    from .services.lesson_access import compute_accessibility

    return compute_accessibility(user, subjects=subjects)


def _resolve_module_entry_slug(module_slug: str, user=None) -> str | None:
    alias_slug = MODULE_LESSON_ALIASES.get(module_slug)
    if alias_slug and Lesson.objects.filter(slug=alias_slug).exists():
        return alias_slug
    module_lessons = list(
        Lesson.objects.filter(module__slug=module_slug).order_by("date", "id")
    )
    if user is not None:
        module_lessons = filter_lessons_for_user_age(module_lessons, user)
    module_lessons = [lesson for lesson in module_lessons if lesson.slug]
    first_lesson = module_lessons[0] if module_lessons else None
    return first_lesson.slug if first_lesson else None


def _resolve_subject_entry_slug(
    subject_names: tuple[str, ...], user=None
) -> str | None:
    subject_lessons: list[Lesson] = []
    for subject_name in subject_names:
        subject_lessons = list(
            Lesson.objects.filter(subject__name__iexact=subject_name).order_by(
                "date", "id"
            )
        )
        if subject_lessons:
            break
    fallback_filters = (
        {"subject__name__icontains": "coding"},
        {"subject__name__icontains": "python"},
        {"slug__startswith": "nivel-"},
    )
    if not subject_lessons:
        for lookup in fallback_filters:
            subject_lessons = list(
                Lesson.objects.filter(**lookup).order_by("date", "id")
            )
            if subject_lessons:
                break
    if not subject_lessons:
        return None
    if user is not None:
        subject_lessons = filter_lessons_for_user_age(subject_lessons, user)
        if get_registration_profile_age(user) is None:
            junior_lessons = [
                lesson
                for lesson in subject_lessons
                if lesson_track_key(lesson) == "junior"
            ]
            if junior_lessons and len(junior_lessons) != len(subject_lessons):
                subject_lessons = junior_lessons
    subject_lessons = [lesson for lesson in subject_lessons if lesson.slug]
    return subject_lessons[0].slug if subject_lessons else None


@login_required
def dashboard_router(request):
    profile = get_profile(request.user)
    if profile.status == ROLE_ADMIN:
        return redirect("estudy:admin_dashboard")
    if profile.status == ROLE_TEACHER:
        return redirect("estudy:teacher_dashboard")
    if profile.status == ROLE_PARENT:
        return redirect("estudy:parent_dashboard")
    return redirect("estudy:student_dashboard")


@login_required
def student_dashboard(request):
    # delegate gathering of dashboard data to service
    from .services.daily_challenge import (
        get_challenge_time_remaining,
        get_todays_challenge,
    )
    from .services.dashboard import build_student_dashboard

    payload = build_student_dashboard(request.user)
    # fetch notifications and leaderboard that are specific to request context
    notifications = Notification.objects.filter(recipient=request.user).order_by(
        "-created_at"
    )[:5]
    leaderboard = get_leaderboard_snapshot(limit=5)
    payload.update({"notifications": notifications, "leaderboard": leaderboard})

    # daily challenge countdown widget
    challenge_result = get_todays_challenge(request.user)
    if challenge_result.success:
        payload["daily_challenge"] = challenge_result.data["challenge"]
        payload["daily_challenge_completed"] = challenge_result.data["completed"]
        payload["daily_challenge_seconds"] = get_challenge_time_remaining()
    else:
        payload["daily_challenge"] = None

    profile = get_profile(request.user)
    replay = request.GET.get("replay") == "1"
    payload["show_onboarding"] = replay or profile.onboarding_completed_at is None
    payload["onboarding_replay"] = replay

    return render(
        request, "estudy/dashboard_student.html", with_progress(payload, request.user)
    )


@login_required
@require_POST
def mark_onboarding_complete(request):
    profile = get_profile(request.user)
    if profile.onboarding_completed_at is None:
        profile.onboarding_completed_at = timezone.now()
        profile.save(update_fields=["onboarding_completed_at"])
    return JsonResponse({"ok": True})


@action_required(ACTION_DASHBOARD_TEACHER)
def teacher_dashboard(request):
    profile = get_profile(request.user)

    # Get lesson analytics overview
    analytics_overview = LessonAnalyticsService.get_lesson_overview_stats(request.user)
    top_lessons = LessonAnalyticsService.get_top_performing_lessons(
        request.user, limit=5
    )

    # Get recent comments and ratings for moderation
    recent_comments = (
        LessonComment.objects.filter(is_approved=False, is_hidden=False)
        .select_related("lesson", "user")
        .order_by("-created_at")[:10]
    )

    recent_ratings = LessonRating.objects.select_related("lesson", "user").order_by(
        "-created_at"
    )[:10]

    context = {
        "profile": profile,
        "analytics_overview": analytics_overview,
        "top_lessons": top_lessons,
        "recent_comments": recent_comments,
        "recent_ratings": recent_ratings,
    }
    return render(
        request, "estudy/dashboard_teacher.html", with_progress(context, request.user)
    )


@action_required(ACTION_MODERATE_COMMENTS)
def moderate_comments(request):
    """View for moderating lesson comments"""
    if request.method == "POST":
        comment_id = request.POST.get("comment_id")
        action = request.POST.get("action")

        try:
            comment = LessonComment.objects.get(id=comment_id)
            if action == "approve":
                comment.is_approved = True
                comment.is_hidden = False
                comment.save()
                messages.success(request, "Comentariul a fost aprobat.")
            elif action == "hide":
                comment.is_hidden = True
                comment.save()
                messages.success(request, "Comentariul a fost ascuns.")
            elif action == "delete":
                comment.delete()
                messages.success(request, "Comentariul a fost șters.")
        except LessonComment.DoesNotExist:
            messages.error(request, "Comentariul nu a fost găsit.")

        return redirect("estudy:moderate_comments")

    # Get comments pending moderation
    pending_comments = (
        LessonComment.objects.filter(is_approved=False)
        .select_related("lesson", "user")
        .order_by("-created_at")
    )

    # Get recent approved comments
    recent_comments = (
        LessonComment.objects.filter(is_approved=True, is_hidden=False)
        .select_related("lesson", "user")
        .order_by("-created_at")[:20]
    )

    context = {
        "pending_comments": pending_comments,
        "recent_comments": recent_comments,
    }

    return render(request, "estudy/moderate_comments.html", context)


@action_required(ACTION_DASHBOARD_ADMIN)
def admin_dashboard(request):
    if Classroom is None:
        raise Http404("Classroom management is not available.")
    lessons = Lesson.objects.select_related("subject").annotate(
        student_count=Count("progress_records")
    )
    top_subjects = Subject.objects.annotate(total=Count("lessons")).order_by("-total")[
        :5
    ]
    total_students = UserProfile.objects.filter(status=ROLE_STUDENT).count()
    total_teachers = UserProfile.objects.filter(status=ROLE_TEACHER).count()
    total_parents = UserProfile.objects.filter(status=ROLE_PARENT).count()
    total_classrooms = Classroom.objects.count()

    context = {
        "lessons": lessons,
        "top_subjects": top_subjects,
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_parents": total_parents,
        "total_classrooms": total_classrooms,
    }
    return render(
        request, "estudy/dashboard_admin.html", with_progress(context, request.user)
    )


@action_required(ACTION_DASHBOARD_PARENT)
def parent_dashboard(request):
    if ParentChildLink is None:
        raise Http404("Parent-child linking is not available.")
    links = ParentChildLink.objects.filter(parent=request.user).select_related("child")
    children = [link.child for link in links]
    child_progress = []
    for child in children:
        progress = build_overall_progress(child)
        child_progress.append(
            {
                "child": child,
                "progress": progress,
                "badges": get_badge_summary(child),
            }
        )
    notifications = Notification.objects.filter(recipient=request.user).order_by(
        "-created_at"
    )[:10]
    context = {"children": child_progress, "notifications": notifications}
    return render(
        request, "estudy/dashboard_parent.html", with_progress(context, request.user)
    )


@login_required
def lessons_list(request):
    query = request.GET.get("q", "").strip()
    subject_filter = request.GET.get("subject", "").strip()
    difficulty_filter = request.GET.get("difficulty", "").strip()
    upcoming_only = request.GET.get("upcoming") == "1"

    # delegate the heavy lifting to the lessons service
    from .services.lessons import prepare_lessons_list

    params = {
        "query": query,
        "subject": subject_filter,
        "difficulty": difficulty_filter,
        "upcoming": upcoming_only,
    }
    context = prepare_lessons_list(request.user, params)
    context["digital_literacy_entry_slug"] = _resolve_module_entry_slug(
        DIGITAL_LITERACY_MODULE_SLUG, request.user
    )
    context["python_entry_slug"] = _resolve_subject_entry_slug(
        PYTHON_TRACK_SUBJECT_NAMES, request.user
    )
    context["learner_age"] = get_registration_profile_age(request.user)
    context["python_mode_label"] = (
        "Junior 8-10 ani"
        if context["learner_age"] is not None and context["learner_age"] <= 10
        else "Code 11+ ani"
        if context["learner_age"] is not None
        else "Junior implicit pana alegi varsta"
    )

    # world map data (learning paths)
    from .services.world_map import build_world_map

    world_map_result = build_world_map(request.user)
    if world_map_result.success:
        context["paths"] = world_map_result.data["paths"]
    else:
        context["paths"] = []

    return render(
        request, "estudy/lessons_list.html", with_progress(context, request.user)
    )


@login_required
def world_map_view(request):
    from .services.world_map import build_world_map

    result = build_world_map(request.user)
    context = {"paths": result.data.get("paths", []) if result.success else []}
    return render(
        request, "estudy/world_map.html", with_progress(context, request.user)
    )


@login_required
def missions_view(request):
    context = {
        "missions": get_mission_context(request.user),
    }
    return render(request, "estudy/missions.html", with_progress(context, request.user))


@login_required
def leaderboard_view(request):
    if Classroom is None or ClassroomMembership is None:
        raise Http404("Classroom leaderboard is not available.")
    classroom_id = request.GET.get("classroom")
    skill_slug = request.GET.get("skill", "").strip()
    leaderboard = get_leaderboard_snapshot(limit=LEADERBOARD_LIMIT)
    skill_summary = None
    if skill_slug:
        from .services.skill_leaderboard import build_skill_leaderboard

        skill_result = build_skill_leaderboard(
            skill_slug=skill_slug,
            limit=LEADERBOARD_LIMIT,
        )
        if skill_result.success:
            leaderboard = skill_result.data["entries"]
            skill_summary = skill_result.data["skill"]
        else:
            messages.error(request, "Skill leaderboard unavailable.")
    classroom = None
    if classroom_id:
        classroom = get_object_or_404(Classroom, pk=classroom_id)
        member_usernames = set(
            ClassroomMembership.objects.filter(classroom=classroom).values_list(
                "user__username", flat=True
            )
        )
        leaderboard = [
            entry for entry in leaderboard if entry["username"] in member_usernames
        ]
    classrooms = ClassroomMembership.objects.filter(user=request.user).select_related(
        "classroom"
    )
    return render(
        request,
        "estudy/leaderboard.html",
        with_progress(
            {
                "leaderboard": leaderboard,
                "classrooms": classrooms,
                "selected_classroom": classroom,
                "skill_summary": skill_summary,
                "skill_slug": skill_slug,
            },
            request.user,
        ),
    )


@login_required
def code_exercise_view(request, pk: int):
    from .models import CodeExercise

    exercise = get_object_or_404(CodeExercise, pk=pk)
    context = {"exercise": exercise}
    return render(
        request, "estudy/code_playground.html", with_progress(context, request.user)
    )


# ── Cooperative session views ─────────────────────────────────────────
@require_POST
@login_required
def coop_create(request):
    from .services.coop import create_coop_session

    lesson_slug = request.POST.get("lesson_slug", "").strip()
    if not lesson_slug:
        return JsonResponse({"error": "lesson_slug is required"}, status=400)
    lesson = get_object_or_404(Lesson, slug=lesson_slug)
    result = create_coop_session(request.user, lesson)
    if not result.success:
        return JsonResponse({"error": result.error}, status=403)
    return JsonResponse(result.data)


@require_POST
@login_required
def coop_join(request):
    from .services.coop import join_coop_session

    session_code = request.POST.get("session_code", "").strip()
    if not session_code:
        return JsonResponse({"error": "session_code is required"}, status=400)
    result = join_coop_session(request.user, session_code)
    if not result.success:
        return JsonResponse({"error": result.error}, status=400)
    return JsonResponse(result.data)


# ── Streak leaderboard per subject ─────────────────────────────────────
@login_required
def streak_leaderboard_view(request, subject_slug):
    from .services.skill_leaderboard import get_streak_leaderboard

    subject = get_object_or_404(Subject, slug=subject_slug)
    result = get_streak_leaderboard(subject, user=request.user)
    if not result.success:
        return JsonResponse({"error": result.error}, status=403)
    return JsonResponse(result.data["entries"], safe=False)


@login_required
@require_POST
def run_code_api(request):
    """Run code against exercise test cases and return JSON with results.

    Expects JSON body with keys:
    - exercise_id: int
    - code: str
    """
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    exercise_id = payload.get("exercise_id")
    code = payload.get("code", "")
    if not exercise_id or not isinstance(exercise_id, int):
        return JsonResponse({"error": "exercise_id is required"}, status=400)
    if not code.strip():
        return JsonResponse({"error": "code is required"}, status=400)

    from .models import CodeExercise  # local import to avoid circulars in module load

    exercise = get_object_or_404(CodeExercise, pk=exercise_id)

    # For now only Python supported
    if exercise.language != "python":
        return JsonResponse(
            {"error": "Only Python is supported in this beta"}, status=400
        )

    result = CodeRunner.run_python_code(code, exercise.test_cases or [])
    from .services.mistake_explanations import build_code_mistake_explanation
    from .services.socratic_followups import build_code_socratic_followups

    explanation_result = build_code_mistake_explanation(result, lesson=exercise.lesson)
    followup_result = build_code_socratic_followups(result, lesson=exercise.lesson)

    similarity_score = None
    suspicious_similarity = False
    similarity_signals = []
    similarity_metadata = {}
    from .services.anti_cheat import CODE_FLAG_SIMILARITY, analyze_code_submission

    similarity_result = analyze_code_submission(
        code=code,
        solution=exercise.solution,
    )
    if similarity_result.success:
        similarity_score = similarity_result.data.get("similarity_score")
        suspicious_similarity = bool(similarity_result.data.get("suspicious"))
        similarity_signals = similarity_result.data.get("signals", [])
        similarity_metadata = similarity_result.data.get("metadata", {})

    # Save submission
    from .models import CodeSubmission

    submission = CodeSubmission.objects.create(
        exercise=exercise,
        user=request.user,
        code=code,
        passed_tests=result.passed,
        total_tests=result.total,
        is_correct=result.is_correct,
        execution_time_ms=result.execution_time_ms,
        output="\n".join(
            [
                f"[{i + 1}] {tr.get('actual', '')}"
                for i, tr in enumerate(result.test_results)
            ]
        )[:4000],
        error_message=(result.error or "")[:1000],
    )

    if suspicious_similarity:
        metadata = {
            "exercise_id": exercise.id,
            "submission_id": submission.id,
            "signals": similarity_signals,
            "flag": CODE_FLAG_SIMILARITY,
        }
        metadata.update(similarity_metadata)
        log_event(
            EventLog.EVENT_TEST_SUBMIT,
            user=request.user,
            metadata=metadata,
        )

    # XP reward on first full pass
    if result.is_correct:
        try:
            # award lesson xp if not completed yet
            lp, _ = LessonProgress.objects.get_or_create(
                user=request.user, lesson=exercise.lesson
            )
            if not lp.completed:
                lp.mark_completed()
        except Exception:
            pass

    resp = result.to_dict()
    if explanation_result.success:
        resp["mistake_explanation"] = explanation_result.data.get("explanation")
    if followup_result.success:
        resp["socratic_questions"] = followup_result.data.get("questions", [])
    resp.update({"submission_id": submission.id, "similarity_score": similarity_score})
    return JsonResponse(resp)


@login_required
def notifications_center(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by(
        "-created_at"
    )
    Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(
        read_at=timezone.now()
    )
    prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = NotificationPreferenceForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            messages.success(request, "Preferintele de notificare au fost actualizate.")
            return redirect("estudy:notifications")
    else:
        form = NotificationPreferenceForm(instance=prefs)
    return render(
        request,
        "estudy/notifications.html",
        with_progress({"notifications": notifications, "form": form}, request.user),
    )


@login_required
def classroom_hub(request):
    if Classroom is None or ClassroomMembership is None or ClassroomForm is None:
        raise Http404("Classroom feature is not available.")
    profile = get_profile(request.user)
    memberships = ClassroomMembership.objects.filter(user=request.user).select_related(
        "classroom"
    )
    classrooms = (
        Classroom.objects.filter(owner=request.user)
        if profile.status == ROLE_TEACHER
        else None
    )
    join_error = None
    if request.method == "POST" and profile.status == ROLE_TEACHER:
        form = ClassroomForm(request.POST)
        if form.is_valid():
            classroom = form.save(commit=False)
            classroom.owner = request.user
            classroom.save()
            messages.success(request, "Clasa a fost creata cu succes.")
            return redirect("estudy:classrooms")
    elif request.method == "POST" and profile.status != ROLE_TEACHER:
        code = request.POST.get("invite_code", "").strip().upper()
        try:
            classroom = Classroom.objects.get(invite_code=code, archived=False)
            ClassroomMembership.objects.get_or_create(
                classroom=classroom, user=request.user
            )
            messages.success(request, f"Te-ai alaturat clasei {classroom.name}!")
            return redirect("estudy:classrooms")
        except Classroom.DoesNotExist:
            join_error = "Cod invalid."
        form = ClassroomForm()
    else:
        form = ClassroomForm()

    return render(
        request,
        "estudy/classrooms.html",
        with_progress(
            {
                "form": form,
                "memberships": memberships,
                "owned": classrooms,
                "join_error": join_error,
                "profile": profile,
            },
            request.user,
        ),
    )


@action_required(ACTION_CLASSROOM_MANAGE)
def classroom_detail(request, pk):
    if (
        Classroom is None
        or ClassroomMembership is None
        or ClassAssignment is None
        or ClassAssignmentForm is None
    ):
        raise Http404("Classroom feature is not available.")
    classroom = get_object_or_404(Classroom, pk=pk, owner=request.user)
    memberships = ClassroomMembership.objects.filter(
        classroom=classroom
    ).select_related("user")
    assignments = ClassAssignment.objects.filter(classroom=classroom).order_by(
        "-created_at"
    )
    if request.method == "POST":
        form = ClassAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.classroom = classroom
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, "Tema a fost publicata.")
            return redirect("estudy:classroom_detail", pk=classroom.pk)
    else:
        form = ClassAssignmentForm()
    return render(
        request,
        "estudy/classroom_detail.html",
        with_progress(
            {
                "classroom": classroom,
                "memberships": memberships,
                "assignments": assignments,
                "form": form,
            },
            request.user,
        ),
    )


@login_required
def projects_view(request):
    if Project is None or ProjectSubmission is None:
        raise Http404("Projects feature is not available.")
    projects = Project.objects.select_related("rubric").order_by("level")
    submissions = ProjectSubmission.objects.filter(student=request.user)
    submitted_ids = list(submissions.values_list("project_id", flat=True))
    return render(
        request,
        "estudy/projects.html",
        with_progress(
            {
                "projects": projects,
                "submitted_project_ids": submitted_ids,
                "project_submissions": submissions,
            },
            request.user,
        ),
    )


@login_required
def submit_project(request, slug):
    if Project is None or ProjectSubmission is None or ProjectSubmissionForm is None:
        raise Http404("Projects feature is not available.")
    project = get_object_or_404(Project, slug=slug)
    submission = ProjectSubmission.objects.filter(
        project=project, student=request.user
    ).first()
    if request.method == "POST":
        form = ProjectSubmissionForm(request.POST, request.FILES, instance=submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.project = project
            submission.student = request.user
            submission.save()
            notify_feedback(
                request.user,
                "Am primit proiectul tau! Profesorii il vor analiza in curand.",
                link_url=reverse("estudy:projects"),
            )
            messages.success(request, "Proiectul a fost trimis.")
            return redirect("estudy:projects")
    else:
        form = ProjectSubmissionForm(instance=submission)
    return render(
        request,
        "estudy/project_submit.html",
        with_progress({"project": project, "form": form}, request.user),
    )


@login_required
def community_forum(request):
    if CommunityThread is None or ThreadForm is None:
        raise Http404("Community forum is not available.")
    threads = CommunityThread.objects.select_related("author").order_by("-created_at")
    if request.method == "POST":
        form = ThreadForm(request.POST)
        if form.is_valid():
            thread = form.save(commit=False)
            thread.author = request.user
            thread.save()
            messages.success(request, "Ai creat un nou subiect de discutie.")
            return redirect("estudy:community")
    else:
        form = ThreadForm()
    return render(
        request,
        "estudy/community.html",
        with_progress({"threads": threads, "form": form}, request.user),
    )


@login_required
def community_thread(request, pk):
    if CommunityThread is None or CommunityReply is None or ReplyForm is None:
        raise Http404("Community forum is not available.")
    thread = get_object_or_404(CommunityThread.objects.select_related("author"), pk=pk)
    replies = CommunityReply.objects.filter(thread=thread).select_related("author")
    if request.method == "POST":
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.thread = thread
            reply.author = request.user
            reply.save()
            send_notification(
                recipient=thread.author,
                title="Cineva a raspuns in comunitate",
                message=f"{request.user.username} a raspuns la {thread.title}",
                category=Notification.CATEGORY_COMMUNITY,
            )
            return redirect("estudy:community_thread", pk=thread.pk)
    else:
        form = ReplyForm()
    return render(
        request,
        "estudy/community_thread.html",
        with_progress(
            {"thread": thread, "replies": replies, "form": form}, request.user
        ),
    )


@login_required
def lesson_module_digital_literacy(request):
    # Keep this route bound to the dedicated interactive template.
    # A generic alias lesson may exist in DB, but this endpoint is the curated module experience.
    context = {
        "module_name": "Modul 1 - Alfabetizare digitala",
        "digital_literacy_entry_slug": _resolve_module_entry_slug(
            DIGITAL_LITERACY_MODULE_SLUG, request.user
        ),
    }
    return render(
        request,
        "estudy/lesson_module_digital_literacy.html",
        with_progress(context, request.user),
    )


@login_required
def typing_game(request):
    return render(request, "estudy/typing_game.html")


@login_required
@ensure_csrf_cookie
def lesson_detail(request, slug):
    try:
        from .services.lesson_detail import (
            BlockingLessonRequired,
            prepare_lesson_detail,
        )

        payload = prepare_lesson_detail(request.user, slug)
        payload["robot_lab_preview"] = (
            _build_robot_lab_lesson_preview(
                request.user, prefer_code_mode=bool(payload.get("show_full_code_lab"))
            )
            if payload.get("show_robot_lab_preview")
            else None
        )
        return render(
            request, "estudy/lesson_detail.html", with_progress(payload, request.user)
        )
    except BlockingLessonRequired as exc:
        messages.info(request, f"Finalizează mai întâi lecția '{exc.blocking_title}'.")
        return redirect("estudy:lesson_detail", slug=exc.blocking_slug)
    except ValueError:
        raise Http404()


@login_required
def share_card_view(request, slug):
    from .services.share_card import build_share_card_context

    lesson = get_object_or_404(Lesson, slug=slug)
    result = build_share_card_context(request.user, lesson)
    if not result.success:
        raise Http404()
    return render(request, "estudy/share_card.html", result.data)


@require_POST
@login_required
def toggle_lesson_completion(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    seconds_spent = request.POST.get("seconds")
    seconds_spent = (
        int(seconds_spent) if seconds_spent and seconds_spent.isdigit() else None
    )
    # delegate to service for testable, centralized behavior
    try:
        from .services.toggles import toggle_lesson_completion_service

        result = toggle_lesson_completion_service(
            request.user, lesson, seconds_spent=seconds_spent
        )
        snapshot = result["progress_snapshot"]
        return JsonResponse(
            {
                "completed": bool(result.get("completed")),
                "progress_percent": snapshot["percent"],
                "completed_count": snapshot["completed"],
                "total_lessons": snapshot["total"],
            }
        )
    except Exception:
        # fallback to legacy inline behavior if service fails for any reason
        from .services.gamification import invalidate_overall_progress_cache

        progress, _ = LessonProgress.objects.get_or_create(
            user=request.user, lesson=lesson
        )

        if progress.completed:
            progress.completed = False
            progress.completed_at = None
            progress.save(update_fields=["completed", "completed_at", "updated_at"])
            invalidate_overall_progress_cache(request.user)
            progress_snapshot = build_overall_progress(request.user)
            return JsonResponse(
                {
                    "completed": False,
                    "progress_percent": progress_snapshot["percent"],
                    "completed_count": progress_snapshot["completed"],
                    "total_lessons": progress_snapshot["total"],
                }
            )

        progress_snapshot = record_lesson_completion(
            request.user, lesson, seconds_spent=seconds_spent
        )
        return JsonResponse(
            {
                "completed": True,
                "progress_percent": progress_snapshot["percent"],
                "completed_count": progress_snapshot["completed"],
                "total_lessons": progress_snapshot["total"],
            }
        )


@require_POST
@login_required
def submit_test_attempt(request, test_id):
    test = get_object_or_404(Test.objects.select_related("lesson"), pk=test_id)
    answer = request.POST.get("answer", "").strip()
    if not answer:
        return JsonResponse({"error": "Trebuie sa alegi un raspuns."}, status=400)

    try:
        from .services.assessment import process_test_attempt

        time_taken = int(request.POST.get("time_taken_ms", "0") or 0)
        response = process_test_attempt(request.user, test, answer, time_taken)
        return JsonResponse(response)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception:
        # fallback to inline behavior to avoid breaking the endpoint
        is_correct = answer == test.correct_answer
        time_taken = int(request.POST.get("time_taken_ms", "0") or 0)
        bonus = bool(
            is_correct
            and time_taken
            and (time_taken / 1000) <= test.bonus_time_threshold
        )
        awarded_points = test.points if is_correct else 0

        attempt, _ = TestAttempt.objects.update_or_create(
            test=test,
            user=request.user,
            defaults={
                "selected_answer": answer,
                "is_correct": is_correct,
                "time_taken_ms": time_taken,
                "awarded_points": awarded_points,
                "earned_bonus": bonus,
                "feedback": test.explanation if not is_correct else "Grozaav!",
            },
        )

        response = {
            "is_correct": is_correct,
            "correct_answer": test.correct_answer,
            "explanation": test.explanation,
            "awarded_points": attempt.awarded_points,
            "earned_bonus": bonus,
        }

        if is_correct:
            progress_snapshot = record_lesson_completion(
                request.user,
                test.lesson,
                seconds_spent=time_taken // 1000 if time_taken else None,
            )
            response.update(
                {
                    "lesson_completed": True,
                    "progress_percent": progress_snapshot["percent"],
                    "completed_count": progress_snapshot["completed"],
                    "total_lessons": progress_snapshot["total"],
                }
            )
        else:
            response["lesson_completed"] = False
            from .services.mistake_explanations import build_test_mistake_explanation
            from .services.socratic_followups import build_test_socratic_followups

            explanation_result = build_test_mistake_explanation(
                test, selected_answer=answer
            )
            if explanation_result.success:
                response["mistake_explanation"] = explanation_result.data.get(
                    "explanation"
                )
            followup_result = build_test_socratic_followups(
                test, selected_answer=answer
            )
            if followup_result.success:
                response["socratic_questions"] = followup_result.data.get(
                    "questions", []
                )

        return JsonResponse(response)


@login_required
def edit_profile(request):
    profile = get_profile(request.user)
    prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=profile)
        prefs_form = NotificationPreferenceForm(request.POST, instance=prefs)
        if profile_form.is_valid() and prefs_form.is_valid():
            profile_form.save()
            prefs_form.save()
            messages.success(request, "Profil actualizat.")
            return redirect("inregistrare_profile")
    else:
        profile_form = ProfileForm(instance=profile)
        prefs_form = NotificationPreferenceForm(instance=prefs)
    return render(
        request,
        "accounts/edit_profile.html",
        with_progress({"form": profile_form, "prefs_form": prefs_form}, request.user),
    )


@login_required
def user_progress(request):
    dată = build_overall_progress(request.user)
    return JsonResponse({"progress_percent": dată["percent"]})


@login_required
def ai_hint(request, slug):
    lesson = get_object_or_404(Lesson, slug=slug)
    question = request.POST.get("question", "").strip()
    if not question:
        return JsonResponse(
            {"error": "Trimite o intrebare pentru a primi un indiciu."}, status=400
        )
    hint = generate_hint(request.user, question, lesson=lesson)
    return JsonResponse({"answer": hint.response})


@login_required
def study_overview(request):
    subjects = Subject.objects.prefetch_related("lessons")
    return render(
        request,
        "estudy/overview.html",
        with_progress(
            {
                "subjects": subjects,
                "progress_percent": build_overall_progress(request.user)["percent"],
            },
            request.user,
        ),
    )


@action_required(ACTION_ANALYTICS_VIEW)
def robot_lab_teacher(request):
    if not _robot_lab_enabled(request.user):
        raise Http404("Robot Lab is not available.")
    from .services.robot_lab_analytics import build_robot_lab_analytics

    filters = {
        "date_from": request.GET.get("date_from", "").strip(),
        "date_to": request.GET.get("date_to", "").strip(),
        "level_id": request.GET.get("level_id", "").strip(),
        "error_type": request.GET.get("error_type", "").strip(),
        "classroom": request.GET.get("classroom", "").strip(),
    }
    payload = build_robot_lab_analytics(filters=filters)
    context = {
        "robot_lab_analytics": payload,
        "robot_lab_filters": filters,
    }
    return render(
        request,
        "estudy/robot_lab_teacher.html",
        with_progress(context, request.user),
    )


@login_required
@ensure_csrf_cookie
def robot_lab_world_map(request):
    """Robo Rescue v2 world map screen."""
    if not _robot_lab_enabled(request.user):
        raise Http404("Robot Lab is not available.")

    from .services.robot_lab_worlds import get_active_skin, list_worlds_with_status

    worlds = list_worlds_with_status(request.user)
    context = {
        "worlds": worlds,
        "worlds_json": json.dumps(worlds),
        "active_skin": get_active_skin(request.user),
    }
    return render(
        request,
        "estudy/robot_lab_world_map.html",
        with_progress(context, request.user),
    )


@login_required
@ensure_csrf_cookie
def robot_lab_game(request, level_id: str):
    """Robo Rescue v2 game screen."""
    if not _robot_lab_enabled(request.user):
        raise Http404("Robot Lab is not available.")

    from .services.robot_lab_levels import (
        RobotLabLevelNotFoundError,
        load_level,
        next_level_id,
    )
    from .services.robot_lab_progress import ensure_robot_lab_progress_rows
    from .services.robot_lab_worlds import get_active_skin

    try:
        level = load_level(level_id)
    except (RobotLabLevelNotFoundError, FileNotFoundError, ValueError):
        raise Http404("Robot Lab level not found.")

    progress_map = ensure_robot_lab_progress_rows(request.user)
    row = progress_map.get(level_id)
    if not row or not row.unlocked:
        messages.error(
            request, "Nivelul este blocat. Finalizează nivelurile anterioare."
        )
        return redirect("estudy:robot_lab_world_map")

    next_id = next_level_id(level_id)
    context = {
        "level": level,
        "level_id": level_id,
        "level_json": json.dumps(
            {
                "id": level.get("id"),
                "title": level.get("title"),
                "goal": level.get("goal") or {},
                "goal_text": level.get("goal_text") or "",
                "grid": level.get("grid") or [],
                "legend": level.get("legend") or {},
                "starter_code": level.get("starter_code") or "",
                "max_steps": int(level.get("max_steps") or 200),
                "xp_reward": int(level.get("xp_reward") or 0),
                "allowed_api": level.get("allowed_api") or [],
                "concepts": level.get("concepts") or [],
                "mode": level.get("mode") or "code",
                "ui_stage": level.get("ui_stage") or "code",
                "start_dir": level.get("start_dir") or "E",
                "world": level.get("world") or 1,
                "world_theme": level.get("world_theme") or "garden",
                "star_conditions": level.get("star_conditions") or {},
                "collectibles": level.get("collectibles") or [],
                "intro_dialog": level.get("intro_dialog") or "",
                "success_dialog": level.get("success_dialog") or "",
                "fail_dialog": level.get("fail_dialog") or "",
                "turtle_enabled": bool(level.get("turtle_enabled")),
            }
        ),
        "level_progress": row,
        "next_level_id": next_id,
        "active_skin": get_active_skin(request.user),
    }
    return render(
        request,
        "estudy/robot_lab_game.html",
        with_progress(context, request.user),
    )
