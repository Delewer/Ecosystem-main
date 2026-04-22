from __future__ import annotations

from typing import Any

from ..models import EventLog
from .audit_logger import log_event
from .service_result import BaseServiceResult

REPUTATION_MIN = 0
REPUTATION_MAX = 10000

TRUSTED_REPUTATION_THRESHOLD = 100
TRUSTED_DEMOTE_THRESHOLD = 50

COMMENT_REWARD = 2
REPLY_REWARD = 1
COMMENT_HIDDEN_PENALTY = -5
COMMENT_LIKE_REWARD = 1
COMMENT_UNLIKE_PENALTY = -1

REASON_COMMENT_APPROVED = "comment_approved"
REASON_COMMENT_HIDDEN = "comment_hidden"
REASON_COMMENT_LIKE = "comment_like"
REASON_COMMENT_UNLIKE = "comment_unlike"
REASON_COMMENT_APPROVED_AFTER_REVIEW = "comment_approved_after_review"

WARNING_NO_PROFILE = "no_profile"
WARNING_SELF_LIKE = "self_like"
WARNING_NO_ACTION = "no_action"

ERROR_MISSING_USER = "User is required"
ERROR_MISSING_COMMENT = "Comment is required"


def _clamp_reputation(score: int) -> int:
    return max(REPUTATION_MIN, min(REPUTATION_MAX, score))


def _get_profile(user):
    return getattr(user, "userprofile", None)


def _update_trusted_status(profile) -> bool:
    if profile.is_trusted_contributor:
        if profile.reputation_score < TRUSTED_DEMOTE_THRESHOLD:
            profile.is_trusted_contributor = False
            return True
        return False
    if profile.reputation_score >= TRUSTED_REPUTATION_THRESHOLD:
        profile.is_trusted_contributor = True
        return True
    return False


def adjust_reputation(
    *,
    user,
    delta: int,
    reason: str,
    metadata: dict[str, Any] | None = None,
) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)
    profile = _get_profile(user)
    if not profile:
        return BaseServiceResult.ok(
            data={"delta": 0, "score": None},
            warnings=[WARNING_NO_PROFILE],
        )

    previous = profile.reputation_score
    next_score = _clamp_reputation(previous + int(delta))
    profile.reputation_score = next_score
    trusted_changed = _update_trusted_status(profile)
    update_fields = ["reputation_score"]
    if trusted_changed:
        update_fields.append("is_trusted_contributor")
    profile.save(update_fields=update_fields)

    log_event(
        EventLog.EVENT_REPUTATION_CHANGE,
        user=user,
        metadata={
            "reason": reason,
            "delta": int(delta),
            "previous_score": previous,
            "new_score": next_score,
            "trusted": profile.is_trusted_contributor,
            "metadata": metadata or {},
        },
    )

    return BaseServiceResult.ok(
        data={
            "delta": int(delta),
            "previous_score": previous,
            "new_score": next_score,
            "trusted": profile.is_trusted_contributor,
        }
    )


def apply_new_comment_reputation(comment) -> BaseServiceResult:
    if comment is None:
        return BaseServiceResult.fail(ERROR_MISSING_COMMENT)
    if comment.is_hidden:
        return adjust_reputation(
            user=comment.user,
            delta=COMMENT_HIDDEN_PENALTY,
            reason=REASON_COMMENT_HIDDEN,
            metadata={"comment_id": comment.id},
        )
    if comment.is_approved:
        reward = REPLY_REWARD if comment.parent_id else COMMENT_REWARD
        return adjust_reputation(
            user=comment.user,
            delta=reward,
            reason=REASON_COMMENT_APPROVED,
            metadata={"comment_id": comment.id, "is_reply": bool(comment.parent_id)},
        )
    return BaseServiceResult.ok(data={"delta": 0}, warnings=[WARNING_NO_ACTION])


def apply_comment_moderation_reputation(
    *,
    comment,
    previous_state: dict[str, bool] | None,
) -> BaseServiceResult:
    if comment is None:
        return BaseServiceResult.fail(ERROR_MISSING_COMMENT)
    if not previous_state:
        return BaseServiceResult.ok(data={"delta": 0}, warnings=[WARNING_NO_ACTION])

    prev_approved = bool(previous_state.get("is_approved"))
    prev_hidden = bool(previous_state.get("is_hidden"))
    if not prev_hidden and comment.is_hidden:
        return adjust_reputation(
            user=comment.user,
            delta=COMMENT_HIDDEN_PENALTY,
            reason=REASON_COMMENT_HIDDEN,
            metadata={"comment_id": comment.id},
        )

    if not prev_approved and comment.is_approved and not comment.is_hidden:
        reward = REPLY_REWARD if comment.parent_id else COMMENT_REWARD
        return adjust_reputation(
            user=comment.user,
            delta=reward,
            reason=REASON_COMMENT_APPROVED_AFTER_REVIEW,
            metadata={"comment_id": comment.id, "is_reply": bool(comment.parent_id)},
        )

    return BaseServiceResult.ok(data={"delta": 0}, warnings=[WARNING_NO_ACTION])


def apply_comment_like_reputation(
    *,
    comment,
    actor=None,
    liked: bool,
) -> BaseServiceResult:
    if comment is None:
        return BaseServiceResult.fail(ERROR_MISSING_COMMENT)
    if actor is not None and comment.user_id == actor.id:
        return BaseServiceResult.ok(data={"delta": 0}, warnings=[WARNING_SELF_LIKE])

    if liked:
        return adjust_reputation(
            user=comment.user,
            delta=COMMENT_LIKE_REWARD,
            reason=REASON_COMMENT_LIKE,
            metadata={"comment_id": comment.id},
        )
    return adjust_reputation(
        user=comment.user,
        delta=COMMENT_UNLIKE_PENALTY,
        reason=REASON_COMMENT_UNLIKE,
        metadata={"comment_id": comment.id},
    )
