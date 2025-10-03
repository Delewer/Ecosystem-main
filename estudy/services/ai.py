from __future__ import annotations

from datetime import datetime

from django.utils import timezone

from ..models import AIHintRequest


def generate_hint(user, question: str, *, lesson=None) -> AIHintRequest:
    playful_answer = "Iti voi oferi un indiciu magic: gandeste-te ce se intampla pas cu pas."
    request = AIHintRequest.objects.create(
        user=user,
        lesson=lesson,
        question=question,
        response=playful_answer,
        resolved_at=timezone.now(),
    )
    return request
