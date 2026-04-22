from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from django.conf import settings
from django.utils import timezone
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.schemas.openapi import SchemaGenerator

DEFAULT_SCHEMA_TITLE = "Ecosystem API"
DEFAULT_SCHEMA_VERSION = "0.1.0"
DEFAULT_SCHEMA_DESCRIPTION = "Auto-generated OpenAPI schema."
DEFAULT_SCHEMA_FORMAT = "json"
SUPPORTED_SCHEMA_FORMATS = {"json", "yaml"}
DEFAULT_OUTPUT_YAML = "docs/openapi.yaml"
DEFAULT_OUTPUT_JSON = "docs/openapi.json"
SORT_KEYS = False
INDENT_SPACES = 2


@dataclass(frozen=True)
class OpenAPISyncResult:
    path: Path
    schema_format: str
    generated_at: timezone.datetime


def _read_schema_settings() -> Mapping[str, Any]:
    return getattr(settings, "ESTUDY_OPENAPI", {}) or {}


def _resolve_schema_metadata() -> tuple[str, str, str]:
    config = _read_schema_settings()
    title = config.get("title") or getattr(
        settings, "ESTUDY_OPENAPI_TITLE", DEFAULT_SCHEMA_TITLE
    )
    version = config.get("version") or getattr(
        settings, "ESTUDY_OPENAPI_VERSION", DEFAULT_SCHEMA_VERSION
    )
    description = config.get("description") or getattr(
        settings, "ESTUDY_OPENAPI_DESCRIPTION", DEFAULT_SCHEMA_DESCRIPTION
    )
    return str(title), str(version), str(description)


def _resolve_format(requested: str | None) -> str:
    if not requested:
        requested = _read_schema_settings().get("format", DEFAULT_SCHEMA_FORMAT)
    normalized = str(requested).lower()
    return (
        normalized if normalized in SUPPORTED_SCHEMA_FORMATS else DEFAULT_SCHEMA_FORMAT
    )


def _resolve_output_path(requested: str | None, schema_format: str) -> Path:
    if requested:
        return Path(requested)
    config_path = _read_schema_settings().get("output_path")
    if config_path:
        return Path(config_path)
    default_path = (
        DEFAULT_OUTPUT_JSON if schema_format == "json" else DEFAULT_OUTPUT_YAML
    )
    return Path(settings.BASE_DIR) / default_path


def _render_schema(schema, schema_format: str) -> bytes:
    renderer = JSONOpenAPIRenderer()
    payload = renderer.render(schema, renderer_context={})
    if schema_format == "json":
        try:
            return json.dumps(
                json.loads(payload.decode("utf-8")),
                indent=INDENT_SPACES,
                sort_keys=SORT_KEYS,
            ).encode("utf-8")
        except json.JSONDecodeError:
            return payload
    try:
        import yaml
    except ImportError:
        return payload
    try:
        data = json.loads(payload.decode("utf-8"))
    except json.JSONDecodeError:
        return payload
    return yaml.safe_dump(data, sort_keys=SORT_KEYS).encode("utf-8")


def generate_openapi_schema() -> bytes:
    title, version, description = _resolve_schema_metadata()
    generator = SchemaGenerator(title=title, version=version, description=description)
    schema = generator.get_schema(request=None, public=True)
    schema_format = _resolve_format(None)
    return _render_schema(schema, schema_format)


def sync_openapi_schema(
    *,
    output_path: str | None = None,
    schema_format: str | None = None,
) -> OpenAPISyncResult:
    format_resolved = _resolve_format(schema_format)
    destination = _resolve_output_path(output_path, format_resolved)
    destination.parent.mkdir(parents=True, exist_ok=True)

    title, version, description = _resolve_schema_metadata()
    generator = SchemaGenerator(title=title, version=version, description=description)
    schema = generator.get_schema(request=None, public=True)
    payload = _render_schema(schema, format_resolved)

    destination.write_bytes(payload)
    return OpenAPISyncResult(
        path=destination,
        schema_format=format_resolved,
        generated_at=timezone.now(),
    )
