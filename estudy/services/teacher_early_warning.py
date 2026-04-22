from __future__ import annotations

from dataclasses import dataclass

from ..models import Classroom, ClassroomMembership
from .notifications_enhanced import NotificationTemplate
from .risk_scoring import (
    RISK_BAND_HIGH,
    RISK_BAND_LOW,
    RISK_BAND_MEDIUM,
    build_student_risk_score,
)
from .service_result import BaseServiceResult

DEFAULT_INCLUDE_BANDS = (RISK_BAND_HIGH, RISK_BAND_MEDIUM)
DEFAULT_MAX_ALERTS = 50
DEFAULT_APPROVED_ONLY = True
DEFAULT_SAMPLE_NAMES = 3
MIN_ALERTS_LIMIT = 0

ALERT_TITLE_KEY = "teacher_early_warning"
ALERT_LINK_TEMPLATE = "/estudy/classrooms/{classroom_id}/"


@dataclass(frozen=True)
class TeacherEarlyWarningAlert:
    student_id: int
    student_username: str
    display_name: str
    risk_score: float
    risk_band: str
    reasons: list[str]
    completion_rate: float
    avg_score: float
    streak_days: int
    last_activity_at: str | None


def _normalize_bands(bands: tuple[str, ...] | None) -> tuple[str, ...]:
    if bands is None:
        return DEFAULT_INCLUDE_BANDS
    return tuple(bands)


def _build_name_summary(alerts: list[TeacherEarlyWarningAlert]) -> str:
    sample_size = min(DEFAULT_SAMPLE_NAMES, len(alerts))
    names = [alert.display_name for alert in alerts[:sample_size]]
    remainder = len(alerts) - sample_size
    summary = ", ".join(names)
    if remainder > 0:
        summary = f"{summary} (+{remainder})"
    return summary


def build_teacher_early_warning_report(
    classroom: Classroom,
    *,
    include_bands: tuple[str, ...] | None = None,
    max_alerts: int = DEFAULT_MAX_ALERTS,
    approved_only: bool = DEFAULT_APPROVED_ONLY,
) -> BaseServiceResult:
    if classroom is None:
        return BaseServiceResult.fail("Classroom is required")

    bands = _normalize_bands(include_bands)
    members = ClassroomMembership.objects.filter(
        classroom=classroom, role=ClassroomMembership.ROLE_STUDENT
    ).select_related("user", "user__userprofile")

    if approved_only:
        members = members.filter(approved=True)

    student_count = members.count()
    if student_count == 0:
        return BaseServiceResult.ok(
            data={
                "alerts": [],
                "summary": {
                    "classroom_id": classroom.id,
                    "classroom_name": classroom.name,
                    "student_count": student_count,
                    "flagged_count": 0,
                    "flagged_by_band": {},
                },
            },
            warnings=["no_students"],
        )

    alerts: list[TeacherEarlyWarningAlert] = []
    flagged_by_band = {RISK_BAND_LOW: 0, RISK_BAND_MEDIUM: 0, RISK_BAND_HIGH: 0}
    warnings: set[str] = set()

    for membership in members:
        student = membership.user
        result = build_student_risk_score(student)
        snapshot = result.data["snapshot"]
        warnings.update(result.warnings)
        flagged_by_band[snapshot.risk_band] = (
            flagged_by_band.get(snapshot.risk_band, 0) + 1
        )

        if snapshot.risk_band not in bands:
            continue

        profile = student.userprofile
        alerts.append(
            TeacherEarlyWarningAlert(
                student_id=student.id,
                student_username=student.username,
                display_name=profile.display_or_username(),
                risk_score=snapshot.risk_score,
                risk_band=snapshot.risk_band,
                reasons=list(snapshot.reasons),
                completion_rate=snapshot.completion_rate,
                avg_score=snapshot.avg_score,
                streak_days=snapshot.streak_days,
                last_activity_at=profile.last_activity_at.isoformat()
                if profile.last_activity_at
                else None,
            )
        )

    alerts.sort(key=lambda item: item.risk_score, reverse=True)
    if max_alerts > MIN_ALERTS_LIMIT:
        alerts = alerts[:max_alerts]

    summary = {
        "classroom_id": classroom.id,
        "classroom_name": classroom.name,
        "student_count": student_count,
        "flagged_count": len(alerts),
        "flagged_by_band": flagged_by_band,
    }

    return BaseServiceResult.ok(
        data={"alerts": alerts, "summary": summary},
        warnings=sorted(warnings),
    )


def send_teacher_early_warning_notification(
    classroom: Classroom,
    *,
    include_bands: tuple[str, ...] | None = None,
    max_alerts: int = DEFAULT_MAX_ALERTS,
) -> BaseServiceResult:
    report = build_teacher_early_warning_report(
        classroom,
        include_bands=include_bands,
        max_alerts=max_alerts,
    )
    if not report.success:
        return report

    alerts = report.data["alerts"]
    if not alerts:
        return BaseServiceResult.ok(
            data={
                "notification": None,
                "alerts": alerts,
                "summary": report.data["summary"],
            },
            warnings=report.warnings,
        )

    names_summary = _build_name_summary(alerts)
    notification = NotificationTemplate.create(
        ALERT_TITLE_KEY,
        recipient=classroom.owner,
        count=len(alerts),
        classroom=classroom.name,
        students=names_summary,
        link_url=ALERT_LINK_TEMPLATE.format(classroom_id=classroom.id),
    )
    return BaseServiceResult.ok(
        data={
            "notification": notification,
            "alerts": alerts,
            "summary": report.data["summary"],
        },
        warnings=report.warnings,
    )
