from pathlib import Path

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

ASSET_FILES = (
    "cartoon/cartoon-map.png",
    "cartoon/cartoon-robot.png",
    "cartoon/cartoon-floor-cell.png",
    "cartoon/cartoon-wall-cell.png",
    "cartoon/cartoon-terminal-cell.png",
    "cartoon/cartoon-door-cell.png",
    "cartoon/cartoon-hazard-cell.png",
    "cartoon/cartoon-portal-cell.png",
    "cartoon/cartoon-battery.png",
    "cartoon/cartoon-key.png",
    "cartoon/cartoon-ui-button-primary.png",
    "cartoon/cartoon-ui-button-secondary.png",
    "cartoon/cartoon-ui-command-button.png",
    "cartoon/cartoon-ui-command-slot.png",
    "cartoon/cartoon-ui-control-panel.png",
)

ROBOT_LAB_FLAGS_ON = {
    "robot_lab_enabled": {
        "enabled": True,
        "rollout_percentage": 100,
    }
}


class RoboRescueGeneratedAssetsTests(SimpleTestCase):
    def setUp(self):
        self.app_dir = Path(__file__).resolve().parent
        self.asset_dir = (
            self.app_dir / "static" / "estudy" / "robot_lab" / "img" / "generated"
        )

    def test_generated_asset_pack_files_exist(self):
        for filename in ASSET_FILES:
            with self.subTest(filename=filename):
                path = self.asset_dir / filename
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 10_000)

    def test_generated_asset_css_references_asset_pack(self):
        css = (
            self.app_dir / "static" / "estudy" / "robot_lab" / "css" / "assets.css"
        ).read_text(encoding="utf-8")

        for filename in ASSET_FILES:
            with self.subTest(filename=filename):
                self.assertIn(filename, css)
        self.assertIn("--rr-asset-robot", css)
        self.assertIn("--rr-asset-floor-cell", css)
        self.assertIn("--rr-asset-hazard: var(--rr-asset-hazard-cell);", css)
        self.assertIn("--rr-asset-portal: var(--rr-asset-portal-cell);", css)
        self.assertIn("--rr-ui-button-primary", css)
        self.assertIn("--rr-ui-command-slot", css)
        self.assertIn("cartoon/", css)
        self.assertIn(".rr-game__controls", css)
        self.assertIn(".rr-sequence__slot.is-filled", css)
        self.assertIn(".rr-robot__sprite", css)
        self.assertIn(".rr-world-map", css)
        self.assertIn(".rr-mission__avatar", css)
        self.assertIn("!important", css)

    def test_robot_lab_templates_load_generated_assets_css(self):
        game_template = (
            self.app_dir / "templates" / "estudy" / "robot_lab_game.html"
        ).read_text(encoding="utf-8")
        world_map_template = (
            self.app_dir / "templates" / "estudy" / "robot_lab_world_map.html"
        ).read_text(encoding="utf-8")

        self.assertIn("robot_lab/css/assets.css", game_template)
        self.assertIn("robot_lab/css/assets.css", world_map_template)
        self.assertIn("20260508c", game_template)
        self.assertIn("20260508c", world_map_template)


@override_settings(ESTUDY_FEATURE_FLAGS=ROBOT_LAB_FLAGS_ON)
class RoboRescueGeneratedAssetsRenderTests(TestCase):
    def test_game_page_renders_busted_asset_stylesheet(self):
        User.objects.create_user(username="rr_asset_student", password="pass1234")
        self.client.login(username="rr_asset_student", password="pass1234")

        response = self.client.get(reverse("estudy:robot_lab_game", args=["W1-L01"]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "robot_lab/css/assets.css")
        self.assertContains(response, "20260508c")
