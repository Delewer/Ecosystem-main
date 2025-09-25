from django import forms
from django.forms import inlineformset_factory

from .models import (
    Lesson,
    LessonPractice,
    LessonResource,
    Test,
    UserProfile,
    default_practice_data,
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
            "theory_intro",
            "theory_takeaways",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "content": forms.Textarea(attrs={"rows": 6}),
            "excerpt": forms.Textarea(attrs={"rows": 3}),
            "theory_intro": forms.Textarea(attrs={"rows": 4}),
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
        fields = ["status"]
