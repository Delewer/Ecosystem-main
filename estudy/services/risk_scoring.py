from __future__ import annotations

from dataclasses import dataclass

from ..models import TestAttempt
from .analytics_summary import get_student_analytics
from .service_result import BaseServiceResult

PERCENT_MIN = 0.0
PERCENT_MAX = 100.0

WEIGHT_COMPLETION = 0.4
WEIGHT_SCORE = 0.4
WEIGHT_STREAK = 0.2
WEIGHT_SUM = WEIGHT_COMPLETION + WEIGHT_SCORE + WEIGHT_STREAK

SCORE_DECIMALS = 2

STREAK_SAFE_DAYS = 7
STREAK_MIN_DAYS = 0

COMPLETION_RISK_THRESHOLD = 50.0
SCORE_RISK_THRESHOLD = 60.0
STREAK_RISK_THRESHOLD = 0

RISK_BAND_LOW = "low"
RISK_BAND_MEDIUM = "medium"
RISK_BAND_HIGH = "high"

RISK_BAND_MEDIUM_MIN = 40.0
RISK_BAND_HIGH_MIN = 70.0


@dataclass(frozen=True)
class StudentRiskSnapshot:
    user_id: int
    risk_score: float
    risk_band: str
    completion_rate: float
    avg_score: float
    streak_days: int
    components: dict
    reasons: list[str]


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _normalize_percent(value: float) -> float:
    return _clamp(value, PERCENT_MIN, PERCENT_MAX)


def _streak_risk(streak_days: int) -> float:
    safe_days = max(STREAK_SAFE_DAYS, 1)
    normalized = max(STREAK_MIN_DAYS, min(streak_days, safe_days))
    return ((safe_days - normalized) / safe_days) * PERCENT_MAX


def _risk_band(score: float) -> str:
    if score >= RISK_BAND_HIGH_MIN:
        return RISK_BAND_HIGH
    if score >= RISK_BAND_MEDIUM_MIN:
        return RISK_BAND_MEDIUM
    return RISK_BAND_LOW


def build_student_risk_score(user) -> BaseServiceResult:
    metrics = get_student_analytics(user)

    completion_rate = float(metrics.get("completion_rate", 0.0))
    avg_score = float(metrics.get("avg_score", 0.0))
    streak_days = int(metrics.get("streak_days", 0))

    completion_risk = PERCENT_MAX - _normalize_percent(completion_rate)
    score_risk = PERCENT_MAX - _normalize_percent(avg_score)
    streak_risk = _normalize_percent(_streak_risk(streak_days))

    if WEIGHT_SUM <= 0:
        risk_score = PERCENT_MIN
    else:
        weighted = (
            completion_risk * WEIGHT_COMPLETION
            + score_risk * WEIGHT_SCORE
            + streak_risk * WEIGHT_STREAK
        )
        risk_score = round(_normalize_percent(weighted / WEIGHT_SUM), SCORE_DECIMALS)

    reasons = []
    if completion_rate < COMPLETION_RISK_THRESHOLD:
        reasons.append("low_completion_rate")
    if avg_score < SCORE_RISK_THRESHOLD:
        reasons.append("low_test_scores")
    if streak_days <= STREAK_RISK_THRESHOLD:
        reasons.append("no_streak")

    warnings = []
    if metrics.get("total_lessons", 0) == 0:
        warnings.append("no_lessons")
    if TestAttempt.objects.filter(user=user).count() == 0:
        warnings.append("no_tests")

    snapshot = StudentRiskSnapshot(
        user_id=user.id,
        risk_score=risk_score,
        risk_band=_risk_band(risk_score),
        completion_rate=completion_rate,
        avg_score=avg_score,
        streak_days=streak_days,
        components={
            "completion_risk": completion_risk,
            "score_risk": score_risk,
            "streak_risk": streak_risk,
        },
        reasons=reasons,
    )

    return BaseServiceResult.ok(
        data={
            "snapshot": snapshot,
            "metrics": metrics,
        },
        warnings=warnings,
    )
