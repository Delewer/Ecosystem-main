from __future__ import annotations

from typing import Dict, Optional

from django.db import transaction
from django.utils import timezone

from ..models import DiagnosticAttempt, DiagnosticTest, LearningPlan, UserProfile
from .gamification import ensure_user_missions
from .learning_paths import build_learning_path, run_entry_diagnostic


def select_learning_goal(user, goal: str) -> UserProfile:
    """Store the learner's goal on signup/preferences."""
    profile = user.userprofile
    valid = {choice[0] for choice in UserProfile.GOAL_CHOICES}
    profile.learning_goal = goal if goal in valid else UserProfile.GOAL_SKILLS
    profile.save(update_fields=["learning_goal"])
    return profile


def get_default_diagnostic_test() -> Optional[DiagnosticTest]:
    """Return the newest diagnostic test if available."""
    return DiagnosticTest.objects.order_by("-created_at").first()


@transaction.atomic
def start_onboarding(user, *, goal: Optional[str] = None) -> Dict:
    """Kick off onboarding: goal, missions, diagnostic, and a 7-day plan."""
    profile = user.userprofile
    if goal:
        select_learning_goal(user, goal)

    if not profile.first_mission_assigned:
        ensure_user_missions(user)
        profile.first_mission_assigned = True
        profile.save(update_fields=["first_mission_assigned"])

    plan = (
        LearningPlan.objects.filter(user=user)
        .order_by("-start_date", "-created_at")
        .first()
    )
    if plan is None:
        plan = build_learning_path(user, days=7)

    diagnostic_test = get_default_diagnostic_test()
    return {
        "profile": profile,
        "learning_plan": plan,
        "diagnostic_test": diagnostic_test,
    }


def complete_diagnostic(
    user, diagnostic_test: DiagnosticTest, score: int
) -> DiagnosticAttempt:
    """Record diagnostic completion and mark onboarding as done."""
    attempt = run_entry_diagnostic(user, diagnostic_test, score)
    profile = user.userprofile
    profile.diagnostic_onboarded = True
    if profile.first_mission_assigned and not profile.onboarding_completed_at:
        profile.onboarding_completed_at = timezone.now()
    profile.save(update_fields=["diagnostic_onboarded", "onboarding_completed_at"])
    return attempt


def onboarding_progress(user) -> Dict[str, int | bool]:
    """Return a simple progress view for onboarding UX."""
    profile = user.userprofile
    steps = [
        bool(profile.learning_goal),
        profile.first_mission_assigned,
        profile.diagnostic_onboarded,
    ]
    percent = int((sum(steps) / len(steps)) * 100)
    return {
        "goal_selected": bool(profile.learning_goal),
        "first_mission_assigned": profile.first_mission_assigned,
        "diagnostic_done": profile.diagnostic_onboarded,
        "percent": percent,
    }
