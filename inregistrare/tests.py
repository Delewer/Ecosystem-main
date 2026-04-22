from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from estudy.models import UserProfile

from .models import Profile


class RegistrationTests(TestCase):
    def test_signup_requires_terms_acceptance(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "elevnou",
                "email": "elevnou@example.com",
                "age": "11",
                "role": UserProfile.ROLE_STUDENT,
                "password1": "ParolaSigura123!",
                "password2": "ParolaSigura123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Trebuie să accepți Termenii și condițiile pentru a crea contul.",
        )
        self.assertFalse(User.objects.filter(username="elevnou").exists())

    def test_signup_stores_age_and_terms(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "ana",
                "email": "ana@example.com",
                "age": "12",
                "role": UserProfile.ROLE_STUDENT,
                "password1": "ParolaSigura123!",
                "password2": "ParolaSigura123!",
                "accept_terms": "on",
            },
        )

        self.assertRedirects(response, reverse("index"))
        user = User.objects.get(username="ana")
        profile = Profile.objects.get(user=user)

        self.assertEqual(profile.age, 12)
        self.assertEqual(profile.email, "ana@example.com")
        self.assertTrue(profile.accepted_terms)
        self.assertEqual(profile.accepted_terms_version, "v1")
        self.assertIsNotNone(profile.accepted_terms_at)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="adminlocal",
            email="adminlocal@example.com",
            password="ParolaSigura123!",
        )
        self.profile = Profile.objects.create(
            user=self.user,
            email="adminlocal@example.com",
            age=14,
            accepted_terms=True,
            accepted_terms_at=timezone.now(),
            accepted_terms_version="v1",
        )
        self.user_profile = self.user.userprofile
        self.user_profile.status = UserProfile.ROLE_ADMIN
        self.user_profile.save(update_fields=["status"])

    def test_profile_edit_updates_age_and_email(self):
        self.client.login(username="adminlocal", password="ParolaSigura123!")

        response = self.client.post(
            reverse("edit_profile"),
            {
                "name": "Administrator Local",
                "email": "adminnou@example.com",
                "phone_number": "069000111",
                "age": "16",
                "bio": "Coordonez platforma în limba română.",
            },
        )

        self.assertRedirects(response, reverse("inregistrare_profile"))
        self.profile.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(self.profile.age, 16)
        self.assertEqual(self.profile.name, "Administrator Local")
        self.assertEqual(self.user.email, "adminnou@example.com")

    def test_legal_pages_and_cookie_banner_are_available(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-cookie-banner")
        self.assertContains(response, reverse("termeni_si_conditii"))
        self.assertContains(response, reverse("politica_cookie"))

        terms_response = self.client.get(reverse("termeni_si_conditii"))
        self.assertContains(terms_response, "Termeni și condiții")

        cookie_response = self.client.get(reverse("politica_cookie"))
        self.assertContains(cookie_response, "Politica cookie")
