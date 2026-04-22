#!/usr/bin/env python
"""
Management command to export analytics data.
Run with: python manage.py export_analytics --kind event_log --format csv
"""
from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from estudy.services.analytics_export import (
    DEFAULT_EXPORT_EXTENSION_BIGQUERY,
    DEFAULT_EXPORT_EXTENSION_CSV,
    DEFAULT_EXPORT_FILENAME,
    DEFAULT_EXPORT_LIMIT,
    DEFAULT_EXPORT_TIMESTAMP_FORMAT,
    DEFAULT_SCHEMA_SUFFIX,
    EXPORT_FORMAT_BIGQUERY,
    EXPORT_FORMAT_CSV,
    SUPPORTED_EXPORT_FORMATS,
    SUPPORTED_EXPORT_KINDS,
    build_bigquery_payload,
    export_analytics_to_csv,
    serialize_bigquery_rows,
)

SCHEMA_JSON_INDENT = 2
SCHEMA_JSON_SORT_KEYS = True


def _default_output_path(kind: str, export_format: str) -> Path:
    timestamp = timezone.now().strftime(DEFAULT_EXPORT_TIMESTAMP_FORMAT)
    extension = DEFAULT_EXPORT_EXTENSION_CSV
    if export_format == EXPORT_FORMAT_BIGQUERY:
        extension = DEFAULT_EXPORT_EXTENSION_BIGQUERY
    return Path(f"{DEFAULT_EXPORT_FILENAME}_{kind}_{timestamp}{extension}")


def _schema_path(output_path: Path, schema_output: str | None) -> Path:
    if schema_output:
        return Path(schema_output)
    return Path(f"{output_path}{DEFAULT_SCHEMA_SUFFIX}")


class Command(BaseCommand):
    help = "Export analytics data to CSV or BigQuery-friendly NDJSON."

    def add_arguments(self, parser):
        parser.add_argument(
            "--kind",
            dest="kind",
            required=True,
            choices=sorted(SUPPORTED_EXPORT_KINDS),
        )
        parser.add_argument(
            "--format",
            dest="export_format",
            default=EXPORT_FORMAT_CSV,
            choices=sorted(SUPPORTED_EXPORT_FORMATS),
        )
        parser.add_argument("--start", dest="start_date", default=None)
        parser.add_argument("--end", dest="end_date", default=None)
        parser.add_argument(
            "--limit", dest="limit", type=int, default=DEFAULT_EXPORT_LIMIT
        )
        parser.add_argument("--output", dest="output_path", default=None)
        parser.add_argument("--schema-output", dest="schema_output", default=None)

    def handle(self, *args, **options):
        kind = options.get("kind")
        export_format = options.get("export_format")
        start_date = options.get("start_date")
        end_date = options.get("end_date")
        limit = options.get("limit")
        output_path = options.get("output_path")

        target_path = (
            Path(output_path)
            if output_path
            else _default_output_path(kind, export_format)
        )

        if export_format == EXPORT_FORMAT_CSV:
            result = export_analytics_to_csv(
                kind=kind,
                start=start_date,
                end=end_date,
                limit=limit,
            )
            if not result.success:
                raise CommandError(result.error or "Export failed")
            target_path.write_text(result.data["csv"], encoding="utf-8")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Wrote {result.data['row_count']} rows to {target_path}"
                )
            )
            return

        if export_format != EXPORT_FORMAT_BIGQUERY:
            raise CommandError("Unsupported export format")

        result = build_bigquery_payload(
            kind=kind,
            start=start_date,
            end=end_date,
            limit=limit,
        )
        if not result.success:
            raise CommandError(result.error or "Export failed")
        target_path.write_text(
            serialize_bigquery_rows(result.data["rows"]),
            encoding="utf-8",
        )
        schema_path = _schema_path(target_path, options.get("schema_output"))
        schema_payload = json.dumps(
            result.data["schema"],
            ensure_ascii=True,
            indent=SCHEMA_JSON_INDENT,
            sort_keys=SCHEMA_JSON_SORT_KEYS,
        )
        schema_path.write_text(schema_payload, encoding="utf-8")
        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote {result.data['row_count']} rows to {target_path}"
            )
        )
        self.stdout.write(self.style.SUCCESS(f"Wrote schema to {schema_path}"))
