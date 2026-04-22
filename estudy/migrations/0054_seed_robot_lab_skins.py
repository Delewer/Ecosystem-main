from django.db import migrations

SKINS = [
    {
        "key": "zipp",
        "name": "ZIPP",
        "unlock_condition": "",
        "svg_file": "robot_zipp.svg",
        "ordering": 0,
    },
    {
        "key": "blaze",
        "name": "BLAZE",
        "unlock_condition": "complete_world_2",
        "svg_file": "robot_blaze.svg",
        "ordering": 1,
    },
    {
        "key": "frosty",
        "name": "FROSTY",
        "unlock_condition": "complete_world_3",
        "svg_file": "robot_frosty.svg",
        "ordering": 2,
    },
    {
        "key": "nova",
        "name": "NOVA",
        "unlock_condition": "complete_world_4",
        "svg_file": "robot_nova.svg",
        "ordering": 3,
    },
    {
        "key": "omega",
        "name": "OMEGA",
        "unlock_condition": "complete_world_5_perfect",
        "svg_file": "robot_omega.svg",
        "ordering": 4,
    },
]


def seed_skins(apps, schema_editor):
    RobotLabSkin = apps.get_model("estudy", "RobotLabSkin")
    for skin in SKINS:
        RobotLabSkin.objects.update_or_create(
            key=skin["key"],
            defaults={
                "name": skin["name"],
                "unlock_condition": skin["unlock_condition"],
                "svg_file": skin["svg_file"],
                "ordering": skin["ordering"],
            },
        )


def unseed_skins(apps, schema_editor):
    RobotLabSkin = apps.get_model("estudy", "RobotLabSkin")
    RobotLabSkin.objects.filter(key__in=[s["key"] for s in SKINS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0053_robotlabskin_robotlablevelprogress_stars_earned_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_skins, unseed_skins),
    ]
