import json
import tempfile
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
