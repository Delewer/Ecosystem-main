#!/usr/bin/env python
"""
Management command to fix lessons with empty slugs.
Run with: python manage.py fix_empty_slugs
"""
from django.core.management.base import BaseCommand

from estudy.models import Lesson


class Command(BaseCommand):
    help = "Fix lessons with empty slugs by generating proper slugs"

    def handle(self, *args, **options):
        lessons_with_empty_slugs = Lesson.objects.filter(slug__in=["", None])
        count = 0

        for lesson in lessons_with_empty_slugs:
            # Force save to trigger slug generation
            lesson.save()
            count += 1
            self.stdout.write(f"Fixed slug for lesson: {lesson.title}")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully fixed {count} lessons with empty slugs")
        )
