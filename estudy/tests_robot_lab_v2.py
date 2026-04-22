"""Tests for Robot Lab v2 — Robo Rescue: world unlock, skin unlock, API endpoints."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import RobotLabLevelProgress, RobotLabSkin, UserRobotLabSkin
from .services.robot_lab_worlds import (
    SKIN_DEFINITIONS,
    check_skin_unlocks,
    ensure_default_skin,
    get_active_skin,
    is_world_unlocked,
    list_skins_with_status,
    list_worlds_with_status,
    select_skin,
)


def _create_test_user(username="testuser"):
    return User.objects.create_user(username=username, password="testpass123")


def _seed_skins():
    """Ensure all skins exist in the DB."""
    for sd in SKIN_DEFINITIONS:
        RobotLabSkin.objects.get_or_create(
            key=sd["key"],
            defaults={
                "name": sd["name"],
                "unlock_condition": sd["unlock_condition"],
                "svg_file": sd["svg_file"],
                "ordering": sd["ordering"],
            },
        )


class WorldUnlockTests(TestCase):
    def setUp(self):
        self.user = _create_test_user()
        _seed_skins()

    def test_world_1_always_unlocked(self):
        self.assertTrue(is_world_unlocked(self.user, 1))

    def test_world_2_locked_by_default(self):
        self.assertFalse(is_world_unlocked(self.user, 2))

    def test_world_2_unlocked_when_world_1_complete(self):
        # Create completed progress rows for all W1 levels
        from .services.robot_lab_levels import ordered_level_ids

        all_ids = ordered_level_ids()
        w1_ids = [lid for lid in all_ids if lid.startswith("W1-")]
        for lid in w1_ids:
            RobotLabLevelProgress.objects.create(
                user=self.user, level_id=lid, unlocked=True, completed=True
            )
        self.assertTrue(is_world_unlocked(self.user, 2))

    def test_world_3_locked_until_world_2_done(self):
        self.assertFalse(is_world_unlocked(self.user, 3))

    def test_list_worlds_returns_all_five(self):
        worlds = list_worlds_with_status(self.user)
        self.assertEqual(len(worlds), 5)
        self.assertTrue(worlds[0]["unlocked"])  # World 1
        self.assertFalse(worlds[1]["unlocked"])  # World 2

    def test_invalid_world_returns_false(self):
        self.assertFalse(is_world_unlocked(self.user, 99))


class SkinUnlockTests(TestCase):
    def setUp(self):
        self.user = _create_test_user()
        _seed_skins()

    def test_ensure_default_skin_creates_zipp(self):
        ensure_default_skin(self.user)
        us = UserRobotLabSkin.objects.filter(user=self.user, skin__key="zipp")
        self.assertTrue(us.exists())
        self.assertTrue(us.first().is_active)

    def test_ensure_default_skin_idempotent(self):
        ensure_default_skin(self.user)
        ensure_default_skin(self.user)
        count = UserRobotLabSkin.objects.filter(
            user=self.user, skin__key="zipp"
        ).count()
        self.assertEqual(count, 1)

    def test_check_skin_unlocks_none_by_default(self):
        newly = check_skin_unlocks(self.user)
        self.assertEqual(newly, [])

    def test_check_skin_unlocks_blaze_on_world2_complete(self):
        from .services.robot_lab_levels import ordered_level_ids

        all_ids = ordered_level_ids()
        w2_ids = [lid for lid in all_ids if lid.startswith("W2-")]
        for lid in w2_ids:
            RobotLabLevelProgress.objects.create(
                user=self.user, level_id=lid, unlocked=True, completed=True
            )
        newly = check_skin_unlocks(self.user)
        self.assertIn("blaze", newly)

    def test_skin_unlock_idempotent(self):
        from .services.robot_lab_levels import ordered_level_ids

        all_ids = ordered_level_ids()
        w2_ids = [lid for lid in all_ids if lid.startswith("W2-")]
        for lid in w2_ids:
            RobotLabLevelProgress.objects.create(
                user=self.user, level_id=lid, unlocked=True, completed=True
            )
        check_skin_unlocks(self.user)
        newly2 = check_skin_unlocks(self.user)
        self.assertEqual(newly2, [])

    def test_get_active_skin_default_is_zipp(self):
        self.assertEqual(get_active_skin(self.user), "zipp")

    def test_select_skin_changes_active(self):
        ensure_default_skin(self.user)
        # Manually unlock blaze
        blaze = RobotLabSkin.objects.get(key="blaze")
        UserRobotLabSkin.objects.create(user=self.user, skin=blaze)
        result = select_skin(self.user, "blaze")
        self.assertEqual(result["key"], "blaze")
        self.assertTrue(result["is_active"])
        # Zipp should no longer be active
        zipp_us = UserRobotLabSkin.objects.get(user=self.user, skin__key="zipp")
        self.assertFalse(zipp_us.is_active)

    def test_select_locked_skin_raises(self):
        ensure_default_skin(self.user)
        with self.assertRaises(ValueError):
            select_skin(self.user, "omega")

    def test_select_nonexistent_skin_raises(self):
        with self.assertRaises(ValueError):
            select_skin(self.user, "nonexistent")

    def test_list_skins_returns_all(self):
        skins = list_skins_with_status(self.user)
        keys = [s["key"] for s in skins]
        self.assertIn("zipp", keys)
        self.assertIn("blaze", keys)
        # Zipp should be unlocked (ensure_default_skin is called)
        zipp = next(s for s in skins if s["key"] == "zipp")
        self.assertTrue(zipp["unlocked"])


class RobotLabV2APITests(TestCase):
    def setUp(self):
        self.user = _create_test_user()
        _seed_skins()
        self.client.login(username="testuser", password="testpass123")

    def test_worlds_api_returns_200(self):
        resp = self.client.get(reverse("estudy:robot_lab_worlds_api"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("worlds", data)
        self.assertEqual(len(data["worlds"]), 5)

    def test_worlds_api_requires_auth(self):
        self.client.logout()
        resp = self.client.get(reverse("estudy:robot_lab_worlds_api"))
        self.assertIn(resp.status_code, [401, 403])

    def test_skins_api_returns_200(self):
        resp = self.client.get(reverse("estudy:robot_lab_skins_api"))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("skins", data)
        self.assertGreater(len(data["skins"]), 0)

    def test_skin_select_api(self):
        ensure_default_skin(self.user)
        resp = self.client.post(
            reverse("estudy:robot_lab_skin_select_api"),
            {"skin_key": "zipp"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["key"], "zipp")
        self.assertTrue(data["is_active"])

    def test_skin_select_api_locked_skin(self):
        resp = self.client.post(
            reverse("estudy:robot_lab_skin_select_api"),
            {"skin_key": "omega"},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_skin_select_api_empty_key(self):
        resp = self.client.post(
            reverse("estudy:robot_lab_skin_select_api"),
            {"skin_key": ""},
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)


class LevelIndexTests(TestCase):
    """Verify the level index loads correctly with all 30 levels."""

    def test_all_30_levels_exist(self):
        from .services.robot_lab_levels import ordered_level_ids

        ids = ordered_level_ids()
        self.assertEqual(len(ids), 30)

    def test_worlds_1_through_5_have_6_levels_each(self):
        from .services.robot_lab_levels import list_level_entries

        entries = list_level_entries()
        for world_id in range(1, 6):
            world_levels = [e for e in entries if e.get("world") == world_id]
            self.assertEqual(
                len(world_levels), 6, f"World {world_id} should have 6 levels"
            )

    def test_each_level_loads(self):
        from .services.robot_lab_levels import load_level, ordered_level_ids

        for lid in ordered_level_ids():
            level = load_level(lid)
            self.assertIn("id", level)
            self.assertIn("grid", level)
            self.assertEqual(level["id"], lid)


class StarsEarnedFieldTests(TestCase):
    def test_stars_earned_default_zero(self):
        user = _create_test_user()
        row = RobotLabLevelProgress.objects.create(
            user=user, level_id="W1-L01", unlocked=True
        )
        self.assertEqual(row.stars_earned, 0)

    def test_stars_earned_max_three(self):
        user = _create_test_user()
        row = RobotLabLevelProgress.objects.create(
            user=user, level_id="W1-L01", unlocked=True, stars_earned=3
        )
        self.assertEqual(row.stars_earned, 3)
