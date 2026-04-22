from __future__ import annotations

from dataclasses import dataclass

from django.utils import timezone

from ..models import Classroom, ParentChildLink
from .analytics_summary import get_student_analytics
from .risk_scoring import build_student_risk_score
from .service_result import BaseServiceResult
from .teacher_analytics import TeacherAnalytics
from .teacher_early_warning import build_teacher_early_warning_report

SUMMARY_DECIMALS = 1

ACTIVITY_RATE_WARNING_THRESHOLD = 50.0
SUCCESS_RATE_WARNING_THRESHOLD = 60.0
SUBMISSION_RATE_WARNING_THRESHOLD = 60.0

COMPLETION_RATE_CONCERN_THRESHOLD = 50.0
AVG_SCORE_CONCERN_THRESHOLD = 60.0
STREAK_CONCERN_THRESHOLD = 0

COMPLETION_RATE_HIGHLIGHT_THRESHOLD = 80.0
AVG_SCORE_HIGHLIGHT_THRESHOLD = 85.0
STREAK_HIGHLIGHT_THRESHOLD = 7

INSIGHT_LOW_ACTIVITY = "low_activity_rate"
INSIGHT_LOW_SUCCESS = "low_success_rate"
INSIGHT_LOW_SUBMISSION = "low_submission_rate"
INSIGHT_RISK_ALERTS = "risk_alerts"

CONCERN_LOW_COMPLETION = "low_completion_rate"
CONCERN_LOW_SCORE = "low_avg_score"
CONCERN_NO_STREAK = "no_streak"

HIGHLIGHT_STRONG_COMPLETION = "strong_completion"
HIGHLIGHT_STRONG_SCORE = "strong_avg_score"
HIGHLIGHT_STRONG_STREAK = "strong_streak"

NO_PARENT_LINK = "parent_link_missing"


@dataclass(frozen=True)
class InsightItem:
    code: str
    message: str
    value: float | int | None = None


def _round_percent(value: float) -> float:
    return round(value, SUMMARY_DECIMALS)


def _append_insight(
    items: list[InsightItem], code: str, message: str, value=None
) -> None:
    items.append(InsightItem(code=code, message=message, value=value))


def build_teacher_insights_summary(
    classroom: Classroom,
    *,
    include_risk_alerts: bool = True,
) -> BaseServiceResult:
    if classroom is None:
        return BaseServiceResult.fail("Classroom is required")

    overview = TeacherAnalytics.get_classroom_overview(classroom)
    insights: list[InsightItem] = []
    recommendations: list[str] = []
    warnings: list[str] = []

    activity_rate = float(overview.get("activity_rate", 0.0))
    success_rate = float(overview.get("avg_success_rate", 0.0))
    submission_rate = float(overview.get("avg_submission_rate", 0.0))

    if activity_rate < ACTIVITY_RATE_WARNING_THRESHOLD:
        _append_insight(
            insights,
            INSIGHT_LOW_ACTIVITY,
            "Activity rate is below target.",
            _round_percent(activity_rate),
        )
        recommendations.append("Plan short check-ins to boost weekly activity.")

    if success_rate < SUCCESS_RATE_WARNING_THRESHOLD:
        _append_insight(
            insights,
            INSIGHT_LOW_SUCCESS,
            "Average success rate is below target.",
            _round_percent(success_rate),
        )
        recommendations.append("Review recent test mistakes and revisit key concepts.")

    if submission_rate < SUBMISSION_RATE_WARNING_THRESHOLD:
        _append_insight(
            insights,
            INSIGHT_LOW_SUBMISSION,
            "Assignment submission rate is below target.",
            _round_percent(submission_rate),
        )
        recommendations.append("Send reminders for missing assignments.")

    risk_summary = None
    if include_risk_alerts:
        risk_report = build_teacher_early_warning_report(classroom)
        warnings.extend(risk_report.warnings)
        if risk_report.success:
            risk_summary = risk_report.data["summary"]
            if risk_summary.get("flagged_count", 0) > 0:
                _append_insight(
                    insights,
                    INSIGHT_RISK_ALERTS,
                    "Some students are flagged as at-risk.",
                    risk_summary.get("flagged_count"),
                )
                recommendations.append("Check flagged students and set support goals.")

    summary = {
        "classroom_id": classroom.id,
        "classroom_name": classroom.name,
        "metrics": {
            "total_students": overview.get("total_students", 0),
            "active_students": overview.get("active_students", 0),
            "activity_rate": _round_percent(activity_rate),
            "avg_success_rate": _round_percent(success_rate),
            "avg_submission_rate": _round_percent(submission_rate),
            "total_assignments": overview.get("total_assignments", 0),
            "total_tests_taken": overview.get("total_tests_taken", 0),
        },
        "risk_summary": risk_summary,
    }

    return BaseServiceResult.ok(
        data={
            "summary": summary,
            "insights": [item.__dict__ for item in insights],
            "recommendations": recommendations,
        },
        warnings=warnings,
    )


def build_parent_progress_summary(parent, child) -> BaseServiceResult:
    if not ParentChildLink.objects.filter(
        parent=parent, child=child, approved=True
    ).exists():
        return BaseServiceResult.fail(NO_PARENT_LINK)

    metrics = get_student_analytics(child)
    risk_result = build_student_risk_score(child)
    if not risk_result.success:
        return risk_result
    risk = risk_result.data["snapshot"]

    completion_rate = float(metrics.get("completion_rate", 0.0))
    avg_score = float(metrics.get("avg_score", 0.0))
    streak_days = int(metrics.get("streak_days", 0))

    concerns: list[InsightItem] = []
    highlights: list[InsightItem] = []

    if completion_rate < COMPLETION_RATE_CONCERN_THRESHOLD:
        _append_insight(
            concerns,
            CONCERN_LOW_COMPLETION,
            "Completion rate is below target.",
            _round_percent(completion_rate),
        )
    if avg_score < AVG_SCORE_CONCERN_THRESHOLD:
        _append_insight(
            concerns,
            CONCERN_LOW_SCORE,
            "Average test score is below target.",
            _round_percent(avg_score),
        )
    if streak_days <= STREAK_CONCERN_THRESHOLD:
        _append_insight(
            concerns,
            CONCERN_NO_STREAK,
            "No active learning streak.",
            streak_days,
        )

    if completion_rate >= COMPLETION_RATE_HIGHLIGHT_THRESHOLD:
        _append_insight(
            highlights,
            HIGHLIGHT_STRONG_COMPLETION,
            "Strong completion progress.",
            _round_percent(completion_rate),
        )
    if avg_score >= AVG_SCORE_HIGHLIGHT_THRESHOLD:
        _append_insight(
            highlights,
            HIGHLIGHT_STRONG_SCORE,
            "Strong average test score.",
            _round_percent(avg_score),
        )
    if streak_days >= STREAK_HIGHLIGHT_THRESHOLD:
        _append_insight(
            highlights,
            HIGHLIGHT_STRONG_STREAK,
            "Great learning streak.",
            streak_days,
        )

    summary = {
        "child_id": child.id,
        "child_username": child.username,
        "generated_at": timezone.now().isoformat(),
        "metrics": {
            "completion_rate": _round_percent(completion_rate),
            "completed_lessons": metrics.get("completed_lessons", 0),
            "total_lessons": metrics.get("total_lessons", 0),
            "avg_score": _round_percent(avg_score),
            "streak_days": streak_days,
        },
        "risk_score": {
            "score": risk.risk_score,
            "band": risk.risk_band,
            "reasons": list(risk.reasons),
        },
    }

    return BaseServiceResult.ok(
        data={
            "summary": summary,
            "concerns": [item.__dict__ for item in concerns],
            "highlights": [item.__dict__ for item in highlights],
        }
    )
