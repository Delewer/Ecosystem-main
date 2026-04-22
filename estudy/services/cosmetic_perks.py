from __future__ import annotations

from typing import Optional

from django.utils import timezone

from ..models import CosmeticPerk, EventLog, UserCosmeticPerk
from .audit_logger import log_event
from .service_result import BaseServiceResult

ERROR_MISSING_USER = "User is required"
ERROR_MISSING_PERK = "Perk is required"
ERROR_UNKNOWN_PERK = "Perk not found"
ERROR_NOT_UNLOCKED = "Perk not unlocked"

WARNING_ALREADY_UNLOCKED = "already_unlocked"
WARNING_ALREADY_EQUIPPED = "already_equipped"
WARNING_NO_PROFILE = "no_profile"
WARNING_NO_ELIGIBLE = "no_eligible_perks"
WARNING_NO_NEW_UNLOCKS = "no_new_unlocks"

SOURCE_LEVEL_MILESTONE = "level_milestone"
SOURCE_MANUAL = "manual"

LEVEL_STARTER = 2
LEVEL_ADVENTURER = 4
LEVEL_LEGEND = 7

DEFAULT_PERKS: tuple[dict, ...] = (
    {
        "slug": "frame-spark",
        "title": "Spark Frame",
        "description": "A bright frame for early explorers.",
        "category": CosmeticPerk.CATEGORY_FRAME,
        "rarity": CosmeticPerk.RARITY_COMMON,
        "accent_color": "#f97316",
        "unlock_min_level": LEVEL_STARTER,
    },
    {
        "slug": "aura-ember",
        "title": "Ember Aura",
        "description": "A warm glow for steady progress.",
        "category": CosmeticPerk.CATEGORY_AURA,
        "rarity": CosmeticPerk.RARITY_RARE,
        "accent_color": "#ef4444",
        "unlock_min_level": LEVEL_ADVENTURER,
    },
    {
        "slug": "background-constellation",
        "title": "Constellation Backdrop",
        "description": "A calm backdrop for top achievers.",
        "category": CosmeticPerk.CATEGORY_BACKGROUND,
        "rarity": CosmeticPerk.RARITY_EPIC,
        "accent_color": "#6366f1",
        "unlock_min_level": LEVEL_LEGEND,
    },
)


def _get_profile(user):
    return getattr(user, "userprofile", None)


def _resolve_perk(
    *, perk: CosmeticPerk | None = None, perk_slug: Optional[str] = None
) -> CosmeticPerk | None:
    if perk is not None:
        return perk
    if not perk_slug:
        return None
    return CosmeticPerk.objects.filter(slug=perk_slug, is_active=True).first()


def _log_cosmetic_event(
    *, event_type: str, user, perk: CosmeticPerk, extra: Optional[dict] = None
) -> None:
    metadata = {"perk_id": perk.id, "perk_slug": perk.slug}
    if extra:
        metadata.update(extra)
    log_event(event_type, user=user, metadata=metadata)


def ensure_default_cosmetic_perks() -> list[CosmeticPerk]:
    perks = []
    for payload in DEFAULT_PERKS:
        perk, _ = CosmeticPerk.objects.get_or_create(
            slug=payload["slug"], defaults=payload
        )
        perks.append(perk)
    return perks


def unlock_cosmetic_perk(
    *,
    user,
    perk: CosmeticPerk | None = None,
    perk_slug: Optional[str] = None,
    source: str = SOURCE_MANUAL,
) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)

    resolved = _resolve_perk(perk=perk, perk_slug=perk_slug)
    if resolved is None:
        return BaseServiceResult.fail(ERROR_UNKNOWN_PERK)

    unlock, created = UserCosmeticPerk.objects.get_or_create(
        user=user, perk=resolved, defaults={"source": source}
    )
    warnings: list[str] = []
    if created:
        _log_cosmetic_event(
            event_type=EventLog.EVENT_COSMETIC_UNLOCK,
            user=user,
            perk=resolved,
            extra={"source": source},
        )
    else:
        warnings.append(WARNING_ALREADY_UNLOCKED)

    return BaseServiceResult.ok(
        data={"unlock": unlock, "created": created},
        warnings=warnings,
    )


def award_cosmetic_perks_for_user(user) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)

    profile = _get_profile(user)
    if profile is None:
        return BaseServiceResult.ok(
            data={"count": 0, "unlocked": []},
            warnings=[WARNING_NO_PROFILE],
        )

    ensure_default_cosmetic_perks()
    eligible = list(
        CosmeticPerk.objects.filter(is_active=True, unlock_min_level__lte=profile.level)
    )
    if not eligible:
        return BaseServiceResult.ok(
            data={"count": 0, "unlocked": []},
            warnings=[WARNING_NO_ELIGIBLE],
        )

    existing_ids = set(
        UserCosmeticPerk.objects.filter(user=user, perk__in=eligible).values_list(
            "perk_id", flat=True
        )
    )
    unlocked: list[UserCosmeticPerk] = []
    for perk in eligible:
        if perk.id in existing_ids:
            continue
        unlock = UserCosmeticPerk.objects.create(
            user=user, perk=perk, source=SOURCE_LEVEL_MILESTONE
        )
        unlocked.append(unlock)
        _log_cosmetic_event(
            event_type=EventLog.EVENT_COSMETIC_UNLOCK,
            user=user,
            perk=perk,
            extra={"source": SOURCE_LEVEL_MILESTONE},
        )

    warnings: list[str] = []
    if not unlocked:
        warnings.append(WARNING_NO_NEW_UNLOCKS)

    return BaseServiceResult.ok(
        data={"count": len(unlocked), "unlocked": unlocked},
        warnings=warnings,
    )


def equip_cosmetic_perk(
    *,
    user,
    perk: CosmeticPerk | None = None,
    perk_slug: Optional[str] = None,
) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)

    resolved = _resolve_perk(perk=perk, perk_slug=perk_slug)
    if resolved is None:
        return BaseServiceResult.fail(ERROR_UNKNOWN_PERK)

    try:
        user_perk = UserCosmeticPerk.objects.get(user=user, perk=resolved)
    except UserCosmeticPerk.DoesNotExist:
        return BaseServiceResult.fail(ERROR_NOT_UNLOCKED)

    warnings: list[str] = []
    if user_perk.is_equipped:
        warnings.append(WARNING_ALREADY_EQUIPPED)
        return BaseServiceResult.ok(
            data={"equipped": False, "perk": user_perk}, warnings=warnings
        )

    UserCosmeticPerk.objects.filter(
        user=user,
        perk__category=resolved.category,
        is_equipped=True,
    ).exclude(pk=user_perk.pk).update(is_equipped=False, equipped_at=None)

    user_perk.is_equipped = True
    user_perk.equipped_at = timezone.now()
    user_perk.save(update_fields=["is_equipped", "equipped_at"])

    _log_cosmetic_event(
        event_type=EventLog.EVENT_COSMETIC_EQUIP,
        user=user,
        perk=resolved,
        extra={"category": resolved.category},
    )
    return BaseServiceResult.ok(
        data={"equipped": True, "perk": user_perk}, warnings=warnings
    )


def list_unlocked_perks(*, user) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)
    perks = list(
        UserCosmeticPerk.objects.filter(user=user)
        .select_related("perk")
        .order_by("-unlocked_at")
    )
    return BaseServiceResult.ok(data={"perks": perks, "count": len(perks)})


def list_equipped_perks(*, user) -> BaseServiceResult:
    if user is None:
        return BaseServiceResult.fail(ERROR_MISSING_USER)
    equipped = list(
        UserCosmeticPerk.objects.filter(user=user, is_equipped=True)
        .select_related("perk")
        .order_by("perk__category")
    )
    return BaseServiceResult.ok(data={"perks": equipped, "count": len(equipped)})
