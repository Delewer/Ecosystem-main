from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("estudy", "0011_badge_classroom_dailychallenge_learningpath_mission_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userprofile",
            name="status",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("student", "Student"),
                    ("professor", "Profesor"),
                    ("admin", "Administrator"),
                    ("parent", "Parinte"),
                ],
                default="student",
                db_index=True,
            ),
        ),
        migrations.AddIndex(
            model_name="lessonprogress",
            index=models.Index(
                fields=["user", "completed"], name="est_lp_user_comp_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["recipient", "read_at"], name="est_not_rec_read_idx"
            ),
        ),
    ]
