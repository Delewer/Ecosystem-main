from django import forms
from django.forms import inlineformset_factory

from .models import (
    Lesson,
    LessonPractice,
    LessonResource,
    Test,
    UserProfile,
    default_practice_data,
    Classroom,
    ClassAssignment,
    Project,
    ProjectSubmission,
    Mission,
    NotificationPreference,
    CommunityThread,
    CommunityReply,
)


class LessonForm(forms.ModelForm):
    theory_takeaways = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Un punct pe linie. Se va afișa ca listă de idei principale.",
    )

    class Meta:
        model = Lesson
        fields = [
            "subject",
            "title",
            "slug",
            "excerpt",
            "content",
            "date",
            "duration_minutes",
            "difficulty",
            "age_bracket",
            "cover_image",
            "xp_reward",
            "fun_fact",
            "featured",
            "hero_theme",
            "hero_emoji",
            "theory_intro",
            "theory_takeaways",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "content": forms.Textarea(attrs={"rows": 6}),
            "excerpt": forms.Textarea(attrs={"rows": 3}),
            "theory_intro": forms.Textarea(attrs={"rows": 4}),
            "fun_fact": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "slug": "Optional. Generated automatically when left blank.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and isinstance(self.instance.theory_takeaways, list):
            self.initial["theory_takeaways"] = "\n".join(self.instance.theory_points())

    def clean_theory_takeaways(self):
        raw_value = self.cleaned_data.get("theory_takeaways", "")
        points = [line.strip() for line in raw_value.splitlines() if line.strip()]
        return points


class LessonResourceForm(forms.ModelForm):
    class Meta:
        model = LessonResource
        fields = ["title", "url", "resource_type", "order"]


LessonResourceFormSet = inlineformset_factory(
    Lesson,
    LessonResource,
    form=LessonResourceForm,
    fields=["title", "url", "resource_type", "order"],
    extra=1,
    can_delete=True,
)


class LessonPracticeForm(forms.ModelForm):
    draggables = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Un element per linie, format: Etichetă | cod_unic",
    )
    drop_targets = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Un container per linie, format: Întrebare | cod_unic_potrivire",
    )

    class Meta:
        model = LessonPractice
        fields = ["intro", "instructions", "success_message"]
        widgets = {
            "intro": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.should_save = False
        self.should_delete = False
        data = self.instance.data if getattr(self.instance, "data", None) else {}
        draggables = []
        targets = []
        if isinstance(data, dict):
            draggables = data.get("draggables", []) or []
            targets = data.get("targets", []) or []
        if draggables:
            self.initial.setdefault(
                "draggables",
                "\n".join(f"{item.get('label', '')} | {item.get('id', '')}" for item in draggables),
            )
        if targets:
            self.initial.setdefault(
                "drop_targets",
                "\n".join(f"{target.get('prompt', '')} | {target.get('accepts', '')}" for target in targets),
            )

    def clean(self):
        cleaned = super().clean()
        draggables_raw = cleaned.get("draggables", "") or ""
        targets_raw = cleaned.get("drop_targets", "") or ""

        draggables = []
        seen_ids = set()
        for idx, line in enumerate(draggables_raw.splitlines()):
            chunk = line.strip()
            if not chunk:
                continue
            if "|" not in chunk:
                raise forms.ValidationError(
                    f"Linia {idx + 1} din elementele glisabile trebuie să conțină simbolul '|'."
                )
            label, value = [part.strip() for part in chunk.split("|", 1)]
            if not label or not value:
                raise forms.ValidationError(
                    f"Linia {idx + 1} din elementele glisabile trebuie să aibă și etichetă și cod."
                )
            if value in seen_ids:
                raise forms.ValidationError(f"Codul '{value}' este folosit de două ori.")
            seen_ids.add(value)
            draggables.append({"id": value, "label": label})

        targets = []
        for idx, line in enumerate(targets_raw.splitlines()):
            chunk = line.strip()
            if not chunk:
                continue
            if "|" not in chunk:
                raise forms.ValidationError(
                    f"Linia {idx + 1} din zonele de potrivire trebuie să conțină simbolul '|'."
                )
            prompt, accepts = [part.strip() for part in chunk.split("|", 1)]
            if accepts and accepts not in seen_ids:
                raise forms.ValidationError(
                    f"Codul '{accepts}' din zona de potrivire (linia {idx + 1}) nu se găsește în lista de elemente glisabile."
                )
            targets.append({"id": f"target-{idx}", "prompt": prompt, "accepts": accepts})

        has_content = bool(draggables and targets)
        text_content = any(
            cleaned.get(field)
            for field in ("intro", "instructions", "success_message")
        )

        if has_content:
            cleaned["data"] = {"draggables": draggables, "targets": targets}
            self.should_save = True
        elif self.instance and self.instance.pk and not has_content and not text_content:
            self.should_delete = True
        else:
            cleaned["data"] = {"draggables": draggables, "targets": targets}
            self.should_save = text_content

        return cleaned

    def save(self, commit=True):
        practice = super().save(commit=False)
        practice.data = self.cleaned_data.get("data", default_practice_data())
        if commit:
            practice.save()
        return practice
class TestForm(forms.ModelForm):
    wrong_answers = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="Provide one incorrect answer per line.",
    )

    class Meta:
        model = Test
        fields = [
            "question",
            "theory_summary",
            "practice_prompt",
            "correct_answer",
            "wrong_answers",
            "explanation",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and isinstance(self.instance.wrong_answers, (list, tuple)):
            self.initial["wrong_answers"] = "\n".join(self.instance.wrong_answers)

    def clean_wrong_answers(self):
        raw_value = self.cleaned_data["wrong_answers"]
        answers = [item.strip() for item in raw_value.splitlines() if item.strip()]
        if not answers:
            raise forms.ValidationError("Provide at least one incorrect answer.")
        return answers


TestFormSet = inlineformset_factory(
    Lesson,
    Test,
    form=TestForm,
    fields=[
        "question",
        "theory_summary",
        "practice_prompt",
        "correct_answer",
        "wrong_answers",
        "explanation",
    ],
    extra=1,
    can_delete=True,
)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "status",
            "display_name",
            "bio",
            "mascot_slug",
            "theme_slug",
            "favorite_subject",
            "weekly_goal",
            "notifications_enabled",
            "parent_email",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
        }


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ["email_enabled", "in_app_enabled", "digest_frequency"]


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class ClassAssignmentForm(forms.ModelForm):
    class Meta:
        model = ClassAssignment
        fields = ["title", "description", "assignment_type", "lesson", "project", "due_date", "points"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "assignment_type": forms.Select(attrs={"class": "form-select"}),
            "lesson": forms.Select(attrs={"class": "form-select"}),
            "project": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "points": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ProjectForm(forms.ModelForm):
    skills = forms.CharField(required=False, help_text="Comma separated skill tags")
    resources = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        help_text="One resource URL per line",
    )

    class Meta:
        model = Project
        fields = [
            "title",
            "slug",
            "summary",
            "brief",
            "level",
            "estimated_minutes",
            "points_reward",
            "lesson",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "summary": forms.TextInput(attrs={"class": "form-control"}),
            "brief": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "level": forms.Select(attrs={"class": "form-select"}),
            "estimated_minutes": forms.NumberInput(attrs={"class": "form-control"}),
            "points_reward": forms.NumberInput(attrs={"class": "form-control"}),
            "lesson": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_skills(self):
        raw = self.cleaned_data.get("skills", "")
        return [item.strip() for item in raw.split(',') if item.strip()]

    def clean_resources(self):
        raw = self.cleaned_data.get("resources", "")
        return [line.strip() for line in raw.splitlines() if line.strip()]

    def save(self, commit=True):
        project = super().save(commit=False)
        if commit:
            project.save()
        skills = self.cleaned_data.get("skills")
        resources = self.cleaned_data.get("resources")
        if skills is not None:
            project.skills = skills
        if resources is not None:
            project.resources = resources
        if commit:
            project.save(update_fields=["skills", "resources"])
        return project


class ProjectSubmissionForm(forms.ModelForm):
    class Meta:
        model = ProjectSubmission
        fields = ["description", "solution_url", "attachment"]
        widgets = {
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "solution_url": forms.URLInput(attrs={"class": "form-control"}),
        }


class MissionForm(forms.ModelForm):
    class Meta:
        model = Mission
        fields = [
            "code",
            "title",
            "description",
            "frequency",
            "target_value",
            "reward_points",
            "reward_badge",
            "icon",
            "color",
            "is_active",
        ]


class ThreadForm(forms.ModelForm):
    tags = forms.CharField(required=False, help_text="Separate tags with commas")

    class Meta:
        model = CommunityThread
        fields = ["title", "body", "tags"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def clean_tags(self):
        raw = self.cleaned_data.get("tags", "")
        return [tag.strip() for tag in raw.split(',') if tag.strip()]


class ReplyForm(forms.ModelForm):
    class Meta:
        model = CommunityReply
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
