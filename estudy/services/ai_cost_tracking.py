from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.conf import settings

from ..models import AIHintRequest, AIUsageCost
from .service_result import BaseServiceResult

DEFAULT_PROVIDER = "internal"
DEFAULT_MODEL = "keyword-hints"
DEFAULT_CURRENCY = "USD"

DEFAULT_CHARS_PER_TOKEN = 4
MIN_CHARS_PER_TOKEN = 1
DEFAULT_MIN_TOKENS = 1
MIN_TOKENS_FLOOR = 0

TOKENS_PER_1K = Decimal("1000")
DEFAULT_COST_PER_1K_PROMPT = Decimal("0.000000")
DEFAULT_COST_PER_1K_COMPLETION = Decimal("0.000000")
COST_DECIMAL_PLACES = Decimal("0.000001")

DETAILS_VERSION = "v1"


@dataclass(frozen=True)
class AICostSnapshot:
    request_id: int
    user_id: int
    provider: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: Decimal
    currency: str
    is_estimated: bool
    details: dict


def _setting(name: str, default):
    return getattr(settings, name, default)


def _normalize_decimal(value, fallback: Decimal) -> Decimal:
    if value is None:
        return fallback
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return fallback


def _normalize_int(value, fallback: int, minimum: int) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(minimum, normalized)


def _estimate_tokens(text: str, chars_per_token: int, min_tokens: int) -> int:
    if not text:
        return 0
    estimated = int(math.ceil(len(text) / chars_per_token))
    return max(min_tokens, estimated)


def _compute_cost(
    prompt_tokens: int,
    completion_tokens: int,
    prompt_rate: Decimal,
    completion_rate: Decimal,
) -> Decimal:
    prompt_cost = (Decimal(prompt_tokens) * prompt_rate) / TOKENS_PER_1K
    completion_cost = (Decimal(completion_tokens) * completion_rate) / TOKENS_PER_1K
    total = prompt_cost + completion_cost
    return total.quantize(COST_DECIMAL_PLACES, rounding=ROUND_HALF_UP)


def build_ai_cost_snapshot(request: AIHintRequest) -> BaseServiceResult:
    if request is None:
        return BaseServiceResult.fail("AI hint request is required")

    prompt_text = request.question or ""
    completion_text = request.response or ""

    chars_per_token = _normalize_int(
        _setting("ESTUDY_AI_COST_CHARS_PER_TOKEN", DEFAULT_CHARS_PER_TOKEN),
        DEFAULT_CHARS_PER_TOKEN,
        MIN_CHARS_PER_TOKEN,
    )
    min_tokens = _normalize_int(
        _setting("ESTUDY_AI_COST_MIN_TOKENS", DEFAULT_MIN_TOKENS),
        DEFAULT_MIN_TOKENS,
        MIN_TOKENS_FLOOR,
    )

    prompt_tokens = _estimate_tokens(prompt_text, chars_per_token, min_tokens)
    completion_tokens = _estimate_tokens(completion_text, chars_per_token, min_tokens)
    total_tokens = prompt_tokens + completion_tokens

    prompt_rate = _normalize_decimal(
        _setting("ESTUDY_AI_COST_PER_1K_PROMPT", DEFAULT_COST_PER_1K_PROMPT),
        DEFAULT_COST_PER_1K_PROMPT,
    )
    completion_rate = _normalize_decimal(
        _setting(
            "ESTUDY_AI_COST_PER_1K_COMPLETION",
            DEFAULT_COST_PER_1K_COMPLETION,
        ),
        DEFAULT_COST_PER_1K_COMPLETION,
    )

    provider = _setting("ESTUDY_AI_COST_PROVIDER", DEFAULT_PROVIDER)
    model_name = _setting("ESTUDY_AI_COST_MODEL", DEFAULT_MODEL)
    currency = _setting("ESTUDY_AI_COST_CURRENCY", DEFAULT_CURRENCY)
    is_estimated = bool(_setting("ESTUDY_AI_COST_ESTIMATED", True))

    cost = _compute_cost(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        prompt_rate=prompt_rate,
        completion_rate=completion_rate,
    )

    details = {
        "version": DETAILS_VERSION,
        "prompt_chars": len(prompt_text),
        "completion_chars": len(completion_text),
        "chars_per_token": chars_per_token,
        "min_tokens": min_tokens,
        "prompt_rate_per_1k": str(prompt_rate),
        "completion_rate_per_1k": str(completion_rate),
    }

    snapshot = AICostSnapshot(
        request_id=request.id,
        user_id=request.user_id,
        provider=str(provider),
        model_name=str(model_name),
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost=cost,
        currency=str(currency),
        is_estimated=is_estimated,
        details=details,
    )
    return BaseServiceResult.ok(data={"snapshot": snapshot})


def record_ai_cost(request: AIHintRequest) -> BaseServiceResult:
    snapshot_result = build_ai_cost_snapshot(request)
    if not snapshot_result.success:
        return snapshot_result

    snapshot = snapshot_result.data["snapshot"]

    usage_cost, _ = AIUsageCost.objects.update_or_create(
        request=request,
        defaults={
            "user": request.user,
            "provider": snapshot.provider,
            "model_name": snapshot.model_name,
            "prompt_tokens": snapshot.prompt_tokens,
            "completion_tokens": snapshot.completion_tokens,
            "total_tokens": snapshot.total_tokens,
            "cost": snapshot.cost,
            "currency": snapshot.currency,
            "is_estimated": snapshot.is_estimated,
            "details": snapshot.details,
        },
    )

    return BaseServiceResult.ok(data={"usage_cost": usage_cost, "snapshot": snapshot})
