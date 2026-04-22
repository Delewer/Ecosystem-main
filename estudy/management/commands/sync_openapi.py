#!/usr/bin/env python
"""
Management command to sync the OpenAPI schema into docs.
Run with: python manage.py sync_openapi
"""
from django.core.management.base import BaseCommand

from estudy.services.openapi_sync import sync_openapi_schema


class Command(BaseCommand):
    help = "Generate and write the OpenAPI schema to docs."

    def add_arguments(self, parser):
        parser.add_argument("--format", dest="schema_format", default=None)
        parser.add_argument("--output", dest="output_path", default=None)

    def handle(self, *args, **options):
        result = sync_openapi_schema(
            output_path=options.get("output_path"),
            schema_format=options.get("schema_format"),
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"OpenAPI schema written to {result.path} ({result.schema_format})."
            )
        )
