#!/usr/bin/env python
"""
Management command to seed demo content.
Run with: python manage.py seed_demo_data
"""
from django.core.management.base import BaseCommand

from estudy.services.seed_demo_data import seed_demo_data


class Command(BaseCommand):
    help = "Seed demo data for lessons, courses, and learning paths."

    def handle(self, *args, **options):
        result = seed_demo_data()
        created = result.created
        totals = result.totals
        self.stdout.write(
            self.style.SUCCESS(
                "Seed complete. " f"Created: {created}. " f"Totals: {totals}."
            )
        )
