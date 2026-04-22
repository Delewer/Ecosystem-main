from __future__ import annotations

from functools import wraps
from typing import Iterable, Optional

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from ..models import UserProfile

ACTION_DASHBOARD_STUDENT = "dashboard.student"
ACTION_DASHBOARD_TEACHER = "dashboard.teacher"
ACTION_DASHBOARD_ADMIN = "dashboard.admin"
ACTION_DASHBOARD_PARENT = "dashboard.parent"
ACTION_CLASSROOM_MANAGE = "classroom.manage"
ACTION_MODERATE_COMMENTS = "moderate.comments"
ACTION_ANALYTICS_VIEW = "analytics.view"
ACTION_COMMUNITY_CURATE = "community.curate"

ROLE_STUDENT = UserProfile.ROLE_STUDENT
ROLE_TEACHER = UserProfile.ROLE_PROFESSOR
ROLE_ADMIN = UserProfile.ROLE_ADMIN
ROLE_PARENT = UserProfile.ROLE_PARENT

PERMISSION_MATRIX: dict[str, frozenset[str]] = {
    ACTION_DASHBOARD_STUDENT: frozenset({ROLE_STUDENT}),
    ACTION_DASHBOARD_TEACHER: frozenset({ROLE_TEACHER}),
    ACTION_DASHBOARD_ADMIN: frozenset({ROLE_ADMIN}),
    ACTION_DASHBOARD_PARENT: frozenset({ROLE_PARENT}),
    ACTION_CLASSROOM_MANAGE: frozenset({ROLE_TEACHER}),
    ACTION_MODERATE_COMMENTS: frozenset({ROLE_TEACHER}),
    ACTION_ANALYTICS_VIEW: frozenset({ROLE_TEACHER, ROLE_ADMIN}),
    ACTION_COMMUNITY_CURATE: frozenset({ROLE_TEACHER, ROLE_ADMIN}),
}


def _normalize_role(role: Optional[str]) -> Optional[str]:
    if role is None:
        return None
    return str(role)


def get_user_role(user) -> Optional[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return None
    status = (
        UserProfile.objects.filter(user_id=user.id)
        .values_list("status", flat=True)
        .first()
    )
    return _normalize_role(status)


def allowed_roles(action: str) -> frozenset[str]:
    return PERMISSION_MATRIX.get(action, frozenset())


def is_action_allowed(role: Optional[str], action: str) -> bool:
    if role is None:
        return False
    return role in allowed_roles(action)


def is_allowed(user, action: str) -> bool:
    return is_action_allowed(get_user_role(user), action)


def missing_roles(action: str, *, roles: Iterable[str]) -> set[str]:
    allowed = allowed_roles(action)
    return set(role for role in roles if role not in allowed)


def action_required(action: str):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if not is_allowed(request.user, action):
                return HttpResponseForbidden()
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
