from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from .models import AIHintRequest, AIUsageCost
from .services.ai import generate_hint
from .services.ai_cost_tracking import record_ai_cost

USER_NAME = "ai_user"
USER_PASSWORD = "pass1234"

PROMPT_TEXT = "abcdefgh"
COMPLETION_TEXT = "wxyz"
CHARS_PER_TOKEN = 4
MIN_TOKENS = 1
PROMPT_TOKENS = 2
COMPLETION_TOKENS = 1
TOTAL_TOKENS = 3

PROMPT_RATE = Decimal("0.002")
COMPLETION_RATE = Decimal("0.003")
EXPECTED_COST = Decimal("0.000007")


class AICostTrackingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username=USER_NAME, password=USER_PASSWORD)

    @override_settings(
        ESTUDY_AI_COST_CHARS_PER_TOKEN=CHARS_PER_TOKEN,
        ESTUDY_AI_COST_MIN_TOKENS=MIN_TOKENS,
        ESTUDY_AI_COST_PER_1K_PROMPT=str(PROMPT_RATE),
        ESTUDY_AI_COST_PER_1K_COMPLETION=str(COMPLETION_RATE),
        ESTUDY_AI_COST_PROVIDER="internal",
        ESTUDY_AI_COST_MODEL="keyword-hints",
        ESTUDY_AI_COST_CURRENCY="USD",
        ESTUDY_AI_COST_ESTIMATED=True,
    )
    def test_record_ai_cost_creates_usage_cost(self):
        request = AIHintRequest.objects.create(
            user=self.user,
            question=PROMPT_TEXT,
            response=COMPLETION_TEXT,
        )

        result = record_ai_cost(request)

        self.assertTrue(result.success)
        self.assertEqual(AIUsageCost.objects.count(), 1)

        usage_cost = result.data["usage_cost"]
        self.assertEqual(usage_cost.prompt_tokens, PROMPT_TOKENS)
        self.assertEqual(usage_cost.completion_tokens, COMPLETION_TOKENS)
        self.assertEqual(usage_cost.total_tokens, TOTAL_TOKENS)
        self.assertEqual(usage_cost.cost, EXPECTED_COST)
        self.assertEqual(usage_cost.currency, "USD")

    def test_generate_hint_creates_usage_cost(self):
        request = generate_hint(self.user, "Need a hint")

        self.assertTrue(AIUsageCost.objects.filter(request=request).exists())
