from django.test import TestCase

from .services.comment_moderation import (
    CAPS_MIN_ALPHA_CHARS,
    EXCESS_PUNCT_MIN,
    MAX_LINKS_ALLOWED,
    MODERATION_ACTION_APPROVE,
    MODERATION_ACTION_HIDE,
    MODERATION_ACTION_REVIEW,
    REPEAT_CHAR_MIN,
    SIGNAL_BANNED_WORD,
    SIGNAL_EXCESSIVE_CAPS,
    SIGNAL_EXCESSIVE_LINKS,
    SIGNAL_EXCESSIVE_PUNCT,
    SIGNAL_REPEATED_CHAR,
    TRUSTED_SCORE_DISCOUNT,
    moderate_comment_content,
)

SAFE_COMMENT = "Thanks for the lesson!"
TOXIC_COMMENT = "You are stupid."
LINK_TEMPLATE = "http://example.com/{idx}"
CAPS_COMMENT = "A" * CAPS_MIN_ALPHA_CHARS
REPEAT_COMMENT = "So" + ("o" * REPEAT_CHAR_MIN)
PUNCT_COMMENT = "!?" * (EXCESS_PUNCT_MIN // 2 + 1)


class CommentModerationTests(TestCase):
    def test_safe_comment_is_approved(self):
        result = moderate_comment_content(content=SAFE_COMMENT)

        self.assertTrue(result.success)
        self.assertEqual(result.data["action"], MODERATION_ACTION_APPROVE)
        self.assertTrue(result.data["is_approved"])
        self.assertFalse(result.data["is_hidden"])
        self.assertEqual(result.data["signals"], [])

    def test_banned_word_triggers_review(self):
        result = moderate_comment_content(content=TOXIC_COMMENT)

        self.assertTrue(result.success)
        self.assertEqual(result.data["action"], MODERATION_ACTION_REVIEW)
        self.assertFalse(result.data["is_approved"])
        self.assertFalse(result.data["is_hidden"])
        self.assertIn(SIGNAL_BANNED_WORD, result.data["signals"])

    def test_multiple_signals_trigger_hide(self):
        links = " ".join(
            LINK_TEMPLATE.format(idx=index) for index in range(MAX_LINKS_ALLOWED + 1)
        )
        content = f"stupid {links}"

        result = moderate_comment_content(content=content)

        self.assertTrue(result.success)
        self.assertEqual(result.data["action"], MODERATION_ACTION_HIDE)
        self.assertFalse(result.data["is_approved"])
        self.assertTrue(result.data["is_hidden"])
        self.assertIn(SIGNAL_BANNED_WORD, result.data["signals"])
        self.assertIn(SIGNAL_EXCESSIVE_LINKS, result.data["signals"])

    def test_caps_trigger_review(self):
        result = moderate_comment_content(content=CAPS_COMMENT)

        self.assertTrue(result.success)
        self.assertEqual(result.data["action"], MODERATION_ACTION_REVIEW)
        self.assertIn(SIGNAL_EXCESSIVE_CAPS, result.data["signals"])

    def test_repeat_char_signal_keeps_approved(self):
        result = moderate_comment_content(content=REPEAT_COMMENT)

        self.assertTrue(result.success)
        self.assertEqual(result.data["action"], MODERATION_ACTION_APPROVE)
        self.assertIn(SIGNAL_REPEATED_CHAR, result.data["signals"])

    def test_excessive_punct_signal_keeps_approved(self):
        result = moderate_comment_content(content=PUNCT_COMMENT)

        self.assertTrue(result.success)
        self.assertEqual(result.data["action"], MODERATION_ACTION_APPROVE)
        self.assertIn(SIGNAL_EXCESSIVE_PUNCT, result.data["signals"])

    def test_trusted_user_reduces_score(self):
        result = moderate_comment_content(
            content=CAPS_COMMENT,
            is_trusted=True,
        )

        self.assertTrue(result.success)
        self.assertEqual(result.data["action"], MODERATION_ACTION_APPROVE)
        self.assertIn(SIGNAL_EXCESSIVE_CAPS, result.data["signals"])
        self.assertGreaterEqual(TRUSTED_SCORE_DISCOUNT, 1)
