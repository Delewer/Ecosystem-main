import json
import tempfile
from collections import Counter
from pathlib import Path

from django.test import TestCase

from .services.openapi_sync import sync_openapi_schema

OPENAPI_KEY = "openapi"


class OpenAPISyncTests(TestCase):
    def test_sync_writes_schema_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "openapi.json"
            result = sync_openapi_schema(
                output_path=str(output_path),
                schema_format="json",
            )

            self.assertTrue(output_path.exists())
            self.assertEqual(result.path, output_path)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertIn(OPENAPI_KEY, payload)

    def test_sync_writes_unique_operation_ids(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "openapi.json"
            sync_openapi_schema(
                output_path=str(output_path),
                schema_format="json",
            )

            payload = json.loads(output_path.read_text(encoding="utf-8"))
            operation_ids = [
                operation["operationId"]
                for path_item in payload.get("paths", {}).values()
                for operation in path_item.values()
                if isinstance(operation, dict) and "operationId" in operation
            ]
            duplicates = [
                operation_id
                for operation_id, count in Counter(operation_ids).items()
                if count > 1
            ]

            self.assertGreater(len(operation_ids), 0)
            self.assertEqual([], duplicates)
