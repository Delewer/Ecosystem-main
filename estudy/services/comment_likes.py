from __future__ import annotations

from ..models import CommentLike
from .reputation import apply_comment_like_reputation
from .service_result import BaseServiceResult

REPUTATION_WARNING = "reputation_update_failed"


def toggle_comment_like_service(*, comment, user) -> BaseServiceResult:
    like, created = CommentLike.objects.get_or_create(comment=comment, user=user)
    liked = created
    if not created:
        like.delete()

    rep_result = apply_comment_like_reputation(comment=comment, actor=user, liked=liked)
    warnings = list(rep_result.warnings)
    if not rep_result.success:
        warnings.append(REPUTATION_WARNING)

    return BaseServiceResult.ok(
        data={
            "liked": liked,
            "likes_count": comment.likes.count(),
            "reputation": rep_result.data if rep_result.success else None,
        },
        warnings=warnings,
        meta={"reputation_error": rep_result.error if not rep_result.success else None},
    )
