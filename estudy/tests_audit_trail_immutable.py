from django.contrib.auth.models import User
from django.test import TestCase

from .models import AuditTrailEntry, EventLog
from .services.audit_trail_immutable import append_audit_entry, verify_audit_trail

USER_PASSWORD = "pass1234"

EVENT_ONE_TYPE = EventLog.EVENT_LOGIN
EVENT_TWO_TYPE = EventLog.EVENT_TEST_SUBMIT

TEST_ID = 1
METADATA_ONE = {"ip": "127.0.0.1"}
METADATA_TWO = {"test_id": TEST_ID}

EXPECTED_ENTRY_COUNT = 2


class AuditTrailImmutableTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="audit_user", password=USER_PASSWORD
        )

    def test_append_builds_chain(self):
        result_one = append_audit_entry(
            event_type=EVENT_ONE_TYPE,
            user=self.user,
            metadata=METADATA_ONE,
        )
        result_two = append_audit_entry(
            event_type=EVENT_TWO_TYPE,
            user=self.user,
            metadata=METADATA_TWO,
        )

        self.assertTrue(result_one.success)
        self.assertTrue(result_two.success)
        self.assertEqual(AuditTrailEntry.objects.count(), EXPECTED_ENTRY_COUNT)

        entry_one = result_one.data["entry"]
        entry_two = result_two.data["entry"]

        self.assertEqual(entry_two.previous_hash, entry_one.record_hash)
        self.assertNotEqual(entry_one.record_hash, entry_two.record_hash)
        self.assertTrue(entry_one.payload_hash)

        verify = verify_audit_trail()
        self.assertTrue(verify.success)
        self.assertTrue(verify.data["valid"])

    def test_verify_detects_tampering(self):
        result = append_audit_entry(
            event_type=EVENT_ONE_TYPE,
            user=self.user,
            metadata=METADATA_ONE,
        )
        entry = result.data["entry"]

        AuditTrailEntry.objects.filter(pk=entry.pk).update(metadata={"ip": "0.0.0.0"})

        verify = verify_audit_trail()
        self.assertFalse(verify.success)
        self.assertFalse(verify.data["valid"])
        self.assertTrue(verify.data["errors"])
