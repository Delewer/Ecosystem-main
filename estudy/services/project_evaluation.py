"""
Service helpers for rubric-based project evaluation.
"""

from typing import Dict

from django.db import transaction

from ..models import ProjectEvaluation, ProjectSubmission, Rubric, RubricCriterion


def evaluate_submission(
    submission: ProjectSubmission,
    evaluator,
    scores: Dict[int, float],
    *,
    rubric: Rubric | None = None,
    comments: str = "",
) -> ProjectEvaluation:
    """
    Persist a project evaluation using rubric criteria scores.

    Args:
        submission: the ProjectSubmission instance being evaluated
        evaluator: User who evaluates
        scores: mapping of criterion_id -> score given
        rubric: optional rubric override (falls back to submission.project.rubric)
        comments: optional evaluator comments
    """
    rubric = rubric or submission.project.rubric
    if rubric is None:
        raise ValueError("Rubric is required to evaluate a submission.")

    criteria = RubricCriterion.objects.filter(rubric=rubric).order_by("order")
    if not criteria.exists():
        raise ValueError("Rubric has no criteria defined.")

    # Calculate weighted total
    weighted_total = 0.0
    total_weight = 0.0
    for criterion in criteria:
        score_value = float(scores.get(criterion.id, 0))
        max_score = criterion.max_score or 1
        weight = criterion.weight or 1.0
        total_weight += weight
        weighted_total += weight * (score_value / max_score)

    normalized_score = (weighted_total / total_weight) * 100 if total_weight else 0.0

    with transaction.atomic():
        submission.score = normalized_score
        submission.status = ProjectSubmission.STATUS_RETURNED
        submission.save(update_fields=["score", "status"])

        evaluation = ProjectEvaluation.objects.create(
            submission=submission,
            rubric=rubric,
            evaluator=evaluator,
            total_score=normalized_score,
            comments=comments,
        )

    return evaluation
