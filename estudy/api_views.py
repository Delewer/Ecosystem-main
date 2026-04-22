from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Lesson, LessonAnalytics, LessonComment, LessonProgress, LessonRating
from .serializers import (
    LessonAnalyticsSerializer,
    LessonCommentSerializer,
    LessonProgressSerializer,
    LessonRatingSerializer,
)
from .services.feature_flags import is_enabled as feature_enabled
from .services.permissions import ACTION_ANALYTICS_VIEW, is_allowed
from .services.robot_lab_levels import (
    RobotLabLevelNotFoundError,
    level_map_size,
    load_level,
)
from .services.robot_lab_mentor import build_robo_mentor_response
from .services.robot_lab_progress import (
    build_robot_lab_progress_summary,
    serialize_robot_lab_levels_with_progress,
)
from .services.robot_lab_runner_client import (
    RobotLabRunnerError,
    RobotLabRunnerUnavailableError,
)
from .services.robot_lab_runs import RobotLabRunBlockedError, run_robot_lab_attempt
from .services.robot_lab_worlds import (
    check_skin_unlocks,
    list_skins_with_status,
    list_worlds_with_status,
    select_skin,
)


class LessonCommentsListCreateView(generics.ListCreateAPIView):
    """API view for listing and creating lesson comments"""

    serializer_class = LessonCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        lesson_slug = self.kwargs.get("lesson_slug")
        lesson = get_object_or_404(Lesson, slug=lesson_slug)

        # Get top-level comments (no parent)
        queryset = (
            LessonComment.objects.filter(
                lesson=lesson, parent__isnull=True, is_approved=True, is_hidden=False
            )
            .select_related("user")
            .prefetch_related("likes", "replies")
        )

        # Annotate with likes and replies count
        queryset = queryset.annotate(
            likes_count=Count("likes"), replies_count=Count("replies")
        ).order_by("-created_at")

        return queryset

    def perform_create(self, serializer):
        lesson_slug = self.kwargs.get("lesson_slug")
        lesson = get_object_or_404(Lesson, slug=lesson_slug)
        from .services.comment_moderation import moderate_comment_content

        content = serializer.validated_data.get("content", "")
        profile = getattr(self.request.user, "userprofile", None)
        moderation = moderate_comment_content(
            content=content,
            is_trusted=bool(getattr(profile, "is_trusted_contributor", False)),
        )
        serializer.save(
            lesson=lesson,
            user=self.request.user,
            is_approved=moderation.data["is_approved"],
            is_hidden=moderation.data["is_hidden"],
        )


class LessonCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating and deleting lesson comments"""

    serializer_class = LessonCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LessonComment.objects.filter(user=self.request.user)


class CommentRepliesView(generics.ListCreateAPIView):
    """API view for comment replies"""

    serializer_class = LessonCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        comment_id = self.kwargs.get("comment_id")
        return (
            LessonComment.objects.filter(
                parent_id=comment_id, is_approved=True, is_hidden=False
            )
            .select_related("user")
            .prefetch_related("likes")
            .order_by("created_at")
        )

    def perform_create(self, serializer):
        comment_id = self.kwargs.get("comment_id")
        parent_comment = get_object_or_404(LessonComment, id=comment_id)
        from .services.comment_moderation import moderate_comment_content

        content = serializer.validated_data.get("content", "")
        profile = getattr(self.request.user, "userprofile", None)
        moderation = moderate_comment_content(
            content=content,
            is_trusted=bool(getattr(profile, "is_trusted_contributor", False)),
        )
        serializer.save(
            lesson=parent_comment.lesson,
            parent=parent_comment,
            user=self.request.user,
            is_approved=moderation.data["is_approved"],
            is_hidden=moderation.data["is_hidden"],
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_comment_like(request, comment_id):
    """Toggle like on a comment"""
    comment = get_object_or_404(LessonComment, id=comment_id)
    from .services.comment_likes import toggle_comment_like_service

    result = toggle_comment_like_service(comment=comment, user=request.user)
    return Response(
        {
            "liked": result.data["liked"],
            "likes_count": result.data["likes_count"],
        }
    )


class LessonRatingCreateView(generics.CreateAPIView):
    """API view for creating lesson ratings"""

    serializer_class = LessonRatingSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        lesson_slug = self.kwargs.get("lesson_slug")
        lesson = get_object_or_404(Lesson, slug=lesson_slug)
        serializer.save(lesson=lesson, user=self.request.user)


class LessonRatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API view for retrieving, updating and deleting lesson ratings"""

    serializer_class = LessonRatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LessonRating.objects.filter(user=self.request.user)


class LessonAnalyticsView(generics.ListAPIView):
    """API view for lesson analytics (teacher only)"""

    serializer_class = LessonAnalyticsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not is_allowed(self.request.user, ACTION_ANALYTICS_VIEW):
            return LessonAnalytics.objects.none()

        lesson_slug = self.kwargs.get("lesson_slug")
        if lesson_slug:
            lesson = get_object_or_404(Lesson, slug=lesson_slug)
            return LessonAnalytics.objects.filter(lesson=lesson).order_by("-date")

        # Return analytics for all lessons if no specific lesson
        return LessonAnalytics.objects.all().order_by("-date")[:100]


class LessonProgressListView(generics.ListAPIView):
    """API view for user's lesson progress"""

    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            LessonProgress.objects.filter(user=self.request.user)
            .select_related("lesson")
            .order_by("-updated_at")
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def lesson_stats(request, lesson_slug):
    """Get comprehensive lesson statistics"""
    lesson = get_object_or_404(Lesson, slug=lesson_slug)

    # Basic stats
    total_views = LessonProgress.objects.filter(lesson=lesson).count()
    completions = LessonProgress.objects.filter(lesson=lesson, completed=True).count()
    completion_rate = (completions / total_views * 100) if total_views > 0 else 0

    # Ratings stats
    ratings = LessonRating.objects.filter(lesson=lesson)
    avg_rating = ratings.aggregate(Avg("rating"))["rating__avg"] or 0
    ratings_count = ratings.count()

    # Comments stats
    comments_count = LessonComment.objects.filter(
        lesson=lesson, is_approved=True, is_hidden=False
    ).count()

    # Recent activity (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_completions = LessonProgress.objects.filter(
        lesson=lesson, completed_at__gte=thirty_days_ago
    ).count()

    return Response(
        {
            "lesson": lesson.title,
            "total_views": total_views,
            "completions": completions,
            "completion_rate": round(completion_rate, 1),
            "avg_rating": round(avg_rating, 1),
            "ratings_count": ratings_count,
            "comments_count": comments_count,
            "recent_completions": recent_completions,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def robot_lab_mentor_feedback(request):
    """Return strict RoboMentor JSON feedback for a Robot Lab run payload."""
    raw_payload = request.data if isinstance(request.data, dict) else dict(request.data)
    response_payload = build_robo_mentor_response(raw_payload, user=request.user)
    return Response(response_payload)


def _robot_lab_enabled_for_user(user) -> bool:
    return feature_enabled("robot_lab_enabled", user=user, default=True)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def robot_lab_levels(request):
    if not _robot_lab_enabled_for_user(request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    payload = serialize_robot_lab_levels_with_progress(request.user)
    return Response({"levels": payload})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def robot_lab_level_detail(request, level_id):
    if not _robot_lab_enabled_for_user(request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    try:
        level = load_level(str(level_id))
    except (RobotLabLevelNotFoundError, FileNotFoundError, ValueError):
        return Response(
            {"detail": "Level not found."}, status=status.HTTP_404_NOT_FOUND
        )

    level_payload = {
        "id": level.get("id"),
        "title": level.get("title"),
        "description": level.get("description") or "",
        "goal": level.get("goal") or {},
        "goal_text": level.get("goal_text") or "",
        "concepts": level.get("concepts") or [],
        "difficulty": level.get("difficulty") or "easy",
        "allowed_api": level.get("allowed_api") or [],
        "max_steps": int(level.get("max_steps") or 200),
        "time_limit_ms": int(level.get("time_limit_ms") or 800),
        "xp_reward": int(level.get("xp_reward") or 0),
        "starter_code": level.get("starter_code") or "",
        "grid": level.get("grid") or [],
        "legend": level.get("legend") or {},
        "map_size": level.get("map_size") or level_map_size(level),
        "mode": level.get("mode") or "code",
        "mode_label": level.get("mode_label") or "Code Mode",
        "ui_stage": level.get("ui_stage") or "code",
        "ui_stage_label": level.get("ui_stage_label") or "Full Code",
        "ui_stage_description": level.get("ui_stage_description") or "",
        "recommended_age": level.get("recommended_age") or "11+",
    }
    return Response(level_payload)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def robot_lab_progress(request):
    if not _robot_lab_enabled_for_user(request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(build_robot_lab_progress_summary(request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def robot_lab_run(request):
    if not _robot_lab_enabled_for_user(request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    payload = request.data if isinstance(request.data, dict) else dict(request.data)
    level_id = str(payload.get("level_id") or "").strip()
    student_code = str(payload.get("student_code") or "").strip()
    if not level_id:
        return Response(
            {"error": "level_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not student_code:
        return Response(
            {"error": "student_code is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        hints_used = int(payload.get("hints_used") or 0)
    except (TypeError, ValueError):
        hints_used = 0

    try:
        result = run_robot_lab_attempt(
            user=request.user,
            level_id=level_id,
            student_code=student_code,
            student_requested_solution=bool(
                payload.get("student_requested_solution", False)
            ),
            hints_used=hints_used,
        )
    except RobotLabRunBlockedError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_403_FORBIDDEN)
    except RobotLabRunnerUnavailableError as exc:
        return Response(
            {
                "error": "Runner service is unavailable.",
                "detail": str(exc),
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except RobotLabRunnerError as exc:
        return Response(
            {
                "error": "Runner execution failed.",
                "detail": str(exc),
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except (RobotLabLevelNotFoundError, FileNotFoundError, ValueError):
        return Response({"error": "Level not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def robot_lab_worlds(request):
    """List all worlds with unlock status and star counts."""
    if not _robot_lab_enabled_for_user(request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    worlds = list_worlds_with_status(request.user)
    return Response({"worlds": worlds})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def robot_lab_skins(request):
    """List all skins with unlock status for the authenticated user."""
    if not _robot_lab_enabled_for_user(request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    # Check if any new skins were earned
    check_skin_unlocks(request.user)
    skins = list_skins_with_status(request.user)
    return Response({"skins": skins})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def robot_lab_skin_select(request):
    """Set a skin as the user's active skin."""
    if not _robot_lab_enabled_for_user(request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    payload = request.data if isinstance(request.data, dict) else dict(request.data)
    skin_key = str(payload.get("skin_key") or "").strip()
    if not skin_key:
        return Response(
            {"error": "skin_key is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        result = select_skin(request.user, skin_key)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(result)
