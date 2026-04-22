from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Lesson, Subject


class DigitalLiteracyModuleViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="module_tester",
            email="module@example.com",
            password="pass1234",
        )
        self.client.login(username="module_tester", password="pass1234")
        self.url = reverse("estudy:lesson_module_digital_literacy")

    def test_module_route_has_step_requirements(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "estudy/lesson_module_digital_literacy.html")
        self.assertContains(response, "lesson-experience")
        self.assertContains(response, 'data-step-requires="hardware-map"')
        self.assertContains(response, 'data-step-requires="hardware-software-match"')
        self.assertContains(response, "data-step-lock-hint")
        self.assertContains(response, "data-step-stars")
        self.assertContains(response, "data-secret-bonus")
        self.assertContains(response, "Cele 3 superputeri ale unui erou digital")
        self.assertContains(response, "Fisa de erou digital")

    def test_module_route_stays_dedicated_even_when_alias_lesson_exists(self):
        subject = Subject.objects.create(name="Alias Subject")
        Lesson.objects.create(
            subject=subject,
            title="Alias Lesson",
            slug="module-alias-existing-test",
            content="Continut test",
            date=timezone.localdate(),
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "estudy/lesson_module_digital_literacy.html")
        self.assertContains(response, "data-step-stars")
