from django.contrib.auth.models import User
from django.test import TestCase

from .models import CosmeticPerk, EventLog, UserCosmeticPerk
from .services.cosmetic_perks import (
    LEVEL_ADVENTURER,
    SOURCE_MANUAL,
    WARNING_ALREADY_UNLOCKED,
    award_cosmetic_perks_for_user,
    equip_cosmetic_perk,
    unlock_cosmetic_perk,
)

USER_PASSWORD = "pass1234"

CUSTOM_PERK_ONE_SLUG = "frame-lumen"
CUSTOM_PERK_TWO_SLUG = "frame-bloom"
CUSTOM_PERK_TITLE_ONE = "Lumen Frame"
CUSTOM_PERK_TITLE_TWO = "Bloom Frame"

EXPECTED_ONE = 1
EXPECTED_TWO = 2

DEFAULT_UNLOCKS_AT_ADVENTURER = 2


class CosmeticPerksTests(TestCase):
    def _create_user(self, username: str) -> User:
        return User.objects.create_user(username=username, password=USER_PASSWORD)

    def _create_perk(self, *, slug: str, title: str) -> CosmeticPerk:
        return CosmeticPerk.objects.create(
            slug=slug,
            title=title,
            category=CosmeticPerk.CATEGORY_FRAME,
            rarity=CosmeticPerk.RARITY_COMMON,
        )

    def test_unlock_cosmetic_perk_creates_event(self):
        user = self._create_user("perk-user")
        perk = self._create_perk(slug=CUSTOM_PERK_ONE_SLUG, title=CUSTOM_PERK_TITLE_ONE)

        result = unlock_cosmetic_perk(user=user, perk=perk, source=SOURCE_MANUAL)

        self.assertTrue(result.success)
        self.assertTrue(result.data["created"])
        self.assertEqual(UserCosmeticPerk.objects.count(), EXPECTED_ONE)
        self.assertEqual(
            EventLog.objects.filter(event_type=EventLog.EVENT_COSMETIC_UNLOCK).count(),
            EXPECTED_ONE,
        )
        unlock = UserCosmeticPerk.objects.get(user=user, perk=perk)
        self.assertEqual(unlock.source, SOURCE_MANUAL)

    def test_unlock_cosmetic_perk_idempotent(self):
        user = self._create_user("perk-user-2")
        perk = self._create_perk(slug=CUSTOM_PERK_TWO_SLUG, title=CUSTOM_PERK_TITLE_TWO)

        first = unlock_cosmetic_perk(user=user, perk=perk, source=SOURCE_MANUAL)
        second = unlock_cosmetic_perk(user=user, perk=perk, source=SOURCE_MANUAL)

        self.assertTrue(first.success)
        self.assertTrue(second.success)
        self.assertIn(WARNING_ALREADY_UNLOCKED, second.warnings)
        self.assertEqual(UserCosmeticPerk.objects.count(), EXPECTED_ONE)
        self.assertEqual(
            EventLog.objects.filter(event_type=EventLog.EVENT_COSMETIC_UNLOCK).count(),
            EXPECTED_ONE,
        )

    def test_award_cosmetic_perks_by_level(self):
        user = self._create_user("perk-user-3")
        profile = user.userprofile
        profile.level = LEVEL_ADVENTURER
        profile.save(update_fields=["level"])

        result = award_cosmetic_perks_for_user(user)

        self.assertTrue(result.success)
        self.assertEqual(result.data["count"], DEFAULT_UNLOCKS_AT_ADVENTURER)
        self.assertEqual(
            UserCosmeticPerk.objects.count(), DEFAULT_UNLOCKS_AT_ADVENTURER
        )
        self.assertEqual(
            EventLog.objects.filter(event_type=EventLog.EVENT_COSMETIC_UNLOCK).count(),
            DEFAULT_UNLOCKS_AT_ADVENTURER,
        )

    def test_equip_cosmetic_perk_switches(self):
        user = self._create_user("perk-user-4")
        perk_one = self._create_perk(slug="frame-alpha", title="Alpha Frame")
        perk_two = self._create_perk(slug="frame-beta", title="Beta Frame")

        unlock_cosmetic_perk(user=user, perk=perk_one, source=SOURCE_MANUAL)
        unlock_cosmetic_perk(user=user, perk=perk_two, source=SOURCE_MANUAL)

        first = equip_cosmetic_perk(user=user, perk=perk_one)
        second = equip_cosmetic_perk(user=user, perk=perk_two)

        self.assertTrue(first.success)
        self.assertTrue(second.success)
        first_unlock = UserCosmeticPerk.objects.get(user=user, perk=perk_one)
        second_unlock = UserCosmeticPerk.objects.get(user=user, perk=perk_two)
        self.assertFalse(first_unlock.is_equipped)
        self.assertTrue(second_unlock.is_equipped)
        self.assertEqual(
            EventLog.objects.filter(event_type=EventLog.EVENT_COSMETIC_EQUIP).count(),
            EXPECTED_TWO,
        )
