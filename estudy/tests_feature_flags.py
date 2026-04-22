import hashlib

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from .models import FeatureFlag
from .services.feature_flags import (
    DEFAULT_ROLLOUT_PERCENT,
    MAX_ROLLOUT_PERCENT,
    META_BUCKET,
    META_DEFAULTED,
    MIN_ROLLOUT_PERCENT,
    ROLLOUT_BUCKETS,
    SOURCE_DEFAULT,
    evaluate_flag,
    get_flag_snapshot,
    is_enabled,
)

DEFAULT_FLAG_KEY = "missing-flag"
DEFAULT_ENABLED = True
DEFAULT_ROLLOUT = DEFAULT_ROLLOUT_PERCENT
HALF_ROLLOUT = MAX_ROLLOUT_PERCENT // 2
EXPECTED_DEFAULTED = True


class FeatureFlagServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="flag-user", password="pass1234")

    def test_db_flag_enabled(self):
        FeatureFlag.objects.create(
            key="new-dashboard",
            enabled=True,
            rollout_percentage=MAX_ROLLOUT_PERCENT,
        )
        self.assertTrue(is_enabled("new-dashboard"))

    def test_db_flag_disabled_overrides_default(self):
        FeatureFlag.objects.create(
            key="new-dashboard",
            enabled=False,
            rollout_percentage=MAX_ROLLOUT_PERCENT,
        )
        self.assertFalse(is_enabled("new-dashboard", default=True))

    def test_rollout_requires_user(self):
        FeatureFlag.objects.create(
            key="beta-flow",
            enabled=True,
            rollout_percentage=MAX_ROLLOUT_PERCENT // 2,
        )
        self.assertFalse(is_enabled("beta-flow", user=None))

    def test_rollout_bucket_is_deterministic(self):
        rollout = MAX_ROLLOUT_PERCENT // 2
        FeatureFlag.objects.create(
            key="beta-flow",
            enabled=True,
            rollout_percentage=rollout,
        )
        expected_bucket = self._bucket("beta-flow", self.user.id)
        expected_enabled = expected_bucket < rollout
        self.assertEqual(is_enabled("beta-flow", user=self.user), expected_enabled)

    @override_settings(ESTUDY_FEATURE_FLAGS={"simple-flag": True})
    def test_settings_flag_simple_bool(self):
        self.assertTrue(is_enabled("simple-flag"))

    @override_settings(
        ESTUDY_FEATURE_FLAGS={
            "flag-with-rollout": {
                "enabled": True,
                "rollout_percentage": MAX_ROLLOUT_PERCENT // 4,
            }
        }
    )
    def test_settings_flag_rollout(self):
        snapshot = get_flag_snapshot("flag-with-rollout")
        self.assertIsNotNone(snapshot)
        self.assertEqual(
            snapshot.rollout_percentage,
            MAX_ROLLOUT_PERCENT // 4,
        )

    @override_settings(
        ESTUDY_FEATURE_FLAGS={
            "flag-invalid-rollout": {"enabled": True, "rollout_percentage": "bad"}
        }
    )
    def test_invalid_rollout_clamps_to_min(self):
        snapshot = get_flag_snapshot("flag-invalid-rollout")
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.rollout_percentage, MIN_ROLLOUT_PERCENT)
        self.assertFalse(is_enabled("flag-invalid-rollout", user=self.user))

    def test_unknown_flag_uses_default(self):
        self.assertTrue(is_enabled("missing-flag", default=True))

    def test_evaluate_flag_defaulted(self):
        result = evaluate_flag(DEFAULT_FLAG_KEY, default=DEFAULT_ENABLED)

        self.assertTrue(result.success)
        self.assertEqual(result.data["enabled"], DEFAULT_ENABLED)
        self.assertEqual(result.data["rollout_percentage"], DEFAULT_ROLLOUT)
        self.assertEqual(result.data["source"], SOURCE_DEFAULT)
        self.assertEqual(result.meta.get(META_DEFAULTED), EXPECTED_DEFAULTED)

    def test_evaluate_flag_rollout_uses_bucket(self):
        FeatureFlag.objects.create(
            key="beta-flow",
            enabled=True,
            rollout_percentage=HALF_ROLLOUT,
        )
        result = evaluate_flag("beta-flow", user=self.user)
        expected_bucket = self._bucket("beta-flow", self.user.id)
        expected_enabled = expected_bucket < HALF_ROLLOUT

        self.assertEqual(result.data["enabled"], expected_enabled)
        self.assertEqual(result.meta.get(META_BUCKET), expected_bucket)

    @staticmethod
    def _bucket(flag_key, user_id):
        payload = f"{flag_key}:{user_id}".encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        return int(digest, 16) % ROLLOUT_BUCKETS
