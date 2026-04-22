from __future__ import annotations

from typing import Any, Dict

from ..models import DailyChallenge, ProjectSubmission
from ..services.gamification import (
    build_overall_progress,
    get_badge_summary,
    get_mission_context,
)
from ..services.recommendations import calculate_recommendations


def build_student_dashboard(user) -> Dict[str, Any]:
    """Gather data for student dashboard in a single place for easier testing and caching."""
    progress = build_overall_progress(user)
    badges = get_badge_summary(user)
    missions = get_mission_context(user)
    recommendations = calculate_recommendations(user, limit=3)
    primary_recommendation = recommendations[0] if recommendations else None
    highlighted_badges = (
        badges.get("highlighted", []) if isinstance(badges, dict) else []
    )
    submissions = ProjectSubmission.objects.filter(student=user).select_related(
        "project"
    )[:3]
    challenges = DailyChallenge.objects.filter(
        start_date__lte=__import__("django").utils.timezone.localdate(),
        end_date__gte=__import__("django").utils.timezone.localdate(),
    )

    return {
        "highlighted_badges": highlighted_badges,
        "primary_recommendation": primary_recommendation,
        "profile": user.userprofile,
        "progress": progress,
        "badges": badges,
        "missions": missions,
        "recommendations": recommendations,
        "recent_projects": submissions,
        "challenges": challenges,
    }
