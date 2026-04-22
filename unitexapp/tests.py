from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

SIGNUP_LINK = 'href="/auth/signup/"'
LOGIN_LINK = 'href="/auth/login/"'


class LandingAuthCtaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="landing_user", password="pw12345"
        )

    def test_anonymous_user_sees_signup_and_login_links(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, SIGNUP_LINK)
        self.assertContains(response, LOGIN_LINK)
        self.assertContains(response, "\u00cenregistrare")
        self.assertContains(response, "Autentificare")

    def test_authenticated_user_does_not_see_signup_or_login_links(self):
        self.client.login(username="landing_user", password="pw12345")
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/estudy/"')
        self.assertContains(response, "Deschide dashboard")
        self.assertNotContains(response, SIGNUP_LINK)
        self.assertNotContains(response, LOGIN_LINK)


class WorkspaceAuthNavigationSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="workspace_user", password="pw12345"
        )
        self.workspace_pages = [
            reverse("estudy:lessons_list"),
            reverse("estudy:missions"),
            reverse("estudy:leaderboard"),
            reverse("estudy:projects"),
            reverse("estudy:community"),
            reverse("inregistrare_profile"),
        ]

    def test_anonymous_user_is_redirected_to_login_on_workspace_pages(self):
        for page_url in self.workspace_pages:
            with self.subTest(page=page_url):
                response = self.client.get(page_url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith("/login/?next="))

    def test_authenticated_user_does_not_see_auth_links_on_workspace_pages(self):
        self.client.login(username="workspace_user", password="pw12345")
        for page_url in self.workspace_pages:
            with self.subTest(page=page_url):
                response = self.client.get(page_url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, SIGNUP_LINK)
                self.assertNotContains(response, LOGIN_LINK)

    def test_authenticated_user_is_redirected_from_login_and_signup_forms(self):
        self.client.login(username="workspace_user", password="pw12345")
        for form_url in (reverse("login"), reverse("signup")):
            with self.subTest(url=form_url):
                response = self.client.get(form_url)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response["Location"], reverse("index"))


class FrontendTextSmokeTests(SimpleTestCase):
    BAD_SEQUENCES = (
        "\u0432\u0402",  # вЂ
        "\u0440\u045f",  # рџ
        "\u00c3",  # Ã
        "\u00c2",  # Â
        "\u00d0",  # Ð
        "\u00d1",  # Ñ
        "\ufffd",  # replacement char
    )
    FILE_SUFFIXES = {".html", ".js", ".css"}

    def _iter_frontend_files(self):
        roots = [
            settings.BASE_DIR / "unitexapp" / "templates",
            settings.BASE_DIR / "estudy" / "templates",
            settings.BASE_DIR / "inregistrare" / "templates",
            settings.BASE_DIR / "unitexapp" / "static",
            settings.BASE_DIR / "estudy" / "static",
            settings.BASE_DIR / "inregistrare" / "static",
        ]
        for root in roots:
            if not root.exists():
                continue
            for file_path in root.rglob("*"):
                if (
                    not file_path.is_file()
                    or file_path.suffix not in self.FILE_SUFFIXES
                ):
                    continue
                if "vendor" in file_path.parts:
                    continue
                yield file_path

    def test_frontend_files_have_no_known_mojibake_sequences(self):
        decode_errors = []
        offenders = []

        for file_path in self._iter_frontend_files():
            rel_path = str(file_path.relative_to(Path(settings.BASE_DIR)))
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                decode_errors.append(rel_path)
                continue
            if any(marker in content for marker in self.BAD_SEQUENCES):
                offenders.append(rel_path)

        self.assertFalse(
            decode_errors,
            f"Non-UTF8 frontend files found: {sorted(decode_errors)}",
        )
        self.assertFalse(
            offenders,
            f"Mojibake-like sequences found in frontend files: {sorted(offenders)}",
        )
