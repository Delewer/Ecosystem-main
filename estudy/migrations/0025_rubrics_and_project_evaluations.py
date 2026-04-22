from __future__ import annotations

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("estudy", "0024_learning_paths_and_diagnostics"),
    ]

    operations = [
        migrations.CreateModel(
            name="Rubric",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ("title",),
            },
        ),
        migrations.CreateModel(
            name="RubricCriterion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=150)),
                ("description", models.TextField(blank=True)),
                ("weight", models.FloatField(default=1.0)),
                ("max_score", models.PositiveIntegerField(default=5)),
                ("order", models.PositiveIntegerField(default=0)),
                (
                    "rubric",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="criteria",
                        to="estudy.rubric",
                    ),
                ),
            ],
            options={
                "ordering": ("rubric", "order"),
            },
        ),
        migrations.AddField(
            model_name="project",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="project",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="project",
            name="rubric",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="projects",
                to="estudy.rubric",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="slug",
            field=models.SlugField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="project",
            name="status",
            field=models.CharField(
                choices=[
                    ("draft", "Draft"),
                    ("active", "Active"),
                    ("retired", "Retired"),
                ],
                default="active",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="projectsubmission",
            name="attempt_no",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="projectsubmission",
            name="feedback",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="projectsubmission",
            name="pre_submit_checklist",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="projectsubmission",
            name="score",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="projectsubmission",
            name="status",
            field=models.CharField(
                choices=[
                    ("submitted", "Submitted"),
                    ("returned", "Returned"),
                    ("accepted", "Accepted"),
                ],
                default="submitted",
                max_length=20,
            ),
        ),
        migrations.AlterModelOptions(
            name="project",
            options={"ordering": ("title",)},
        ),
        migrations.AlterModelOptions(
            name="projectsubmission",
            options={"ordering": ("-uploaded_at",)},
        ),
        migrations.AlterUniqueTogether(
            name="projectsubmission",
            unique_together={("student", "project", "attempt_no")},
        ),
        migrations.CreateModel(
            name="ProjectEvaluation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("total_score", models.FloatField(default=0.0)),
                ("comments", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "evaluator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="project_evaluations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "rubric",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="evaluations",
                        to="estudy.rubric",
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="evaluations",
                        to="estudy.projectsubmission",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
    ]
