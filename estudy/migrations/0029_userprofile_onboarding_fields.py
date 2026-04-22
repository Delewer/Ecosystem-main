from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0028_peer_review"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="diagnostic_onboarded",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="first_mission_assigned",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="learning_goal",
            field=models.CharField(
                choices=[
                    ("skills", "Build skills"),
                    ("grades", "Improve grades"),
                    ("career", "Career prep"),
                    ("fun", "Learn for fun"),
                ],
                default="skills",
                max_length=30,
            ),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="onboarding_completed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="preferred_locale",
            field=models.CharField(default="en", max_length=10),
        ),
    ]
