from django import forms

from .models import (
    ClassAssignment,
    Classroom,
    CommunityReply,
    CommunityThread,
    Lesson,
    LessonMedia,
    LessonPractice,
    LessonResource,
    NotificationPreference,
    ProjectSubmission,
    Test,
    UserProfile,
)


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = [
            "subject",
            "title",
            "excerpt",
            "content",
            "date",
            "duration_minutes",
            "difficulty",
            "lesson_type",
            "cover_image",
            "age_bracket",
            "theory_intro",
            "theory_takeaways",
            "xp_reward",
            "fun_fact",
            "featured",
            "hero_theme",
            "hero_emoji",
        ]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 10}),
            "theory_intro": forms.Textarea(attrs={"rows": 5}),
            "theory_takeaways": forms.Textarea(attrs={"rows": 5}),
            "fun_fact": forms.Textarea(attrs={"rows": 3}),
            "date": forms.DateInput(attrs={"type": "date"}),
        }


class LessonMediaForm(forms.ModelForm):
    class Meta:
        model = LessonMedia
        fields = [
            "video_url",
            "video_platform",
            "video_duration_seconds",
            "video_thumbnail",
            "audio_url",
            "audio_duration_seconds",
            "slides_url",
            "slides_count",
        ]
        widgets = {
            "video_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://youtube.com/...",
                }
            ),
            "video_platform": forms.Select(attrs={"class": "form-select"}),
            "video_duration_seconds": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "video_thumbnail": forms.FileInput(attrs={"class": "form-control"}),
            "audio_url": forms.URLInput(attrs={"class": "form-control"}),
            "audio_duration_seconds": forms.NumberInput(
                attrs={"class": "form-control"}
            ),
            "slides_url": forms.URLInput(attrs={"class": "form-control"}),
            "slides_count": forms.NumberInput(attrs={"class": "form-control"}),
        }


class LessonResourceForm(forms.ModelForm):
    class Meta:
        model = LessonResource
        fields = ["title", "url", "resource_type", "order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "url": forms.URLInput(attrs={"class": "form-control"}),
            "resource_type": forms.Select(attrs={"class": "form-select"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class LessonPracticeForm(forms.ModelForm):
    class Meta:
        model = LessonPractice
        fields = ["intro", "instructions", "success_message", "data"]
        widgets = {
            "intro": forms.Textarea(attrs={"rows": 3}),
            "instructions": forms.TextInput(attrs={"class": "form-control"}),
            "success_message": forms.TextInput(attrs={"class": "form-control"}),
            "data": forms.HiddenInput(),
        }


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = [
            "question",
            "correct_answer",
            "wrong_answers",
            "theory_summary",
            "practice_prompt",
            "explanation",
            "difficulty",
            "time_limit_seconds",
            "points",
            "bonus_time_threshold",
        ]
        widgets = {
            "question": forms.TextInput(attrs={"class": "form-control"}),
            "correct_answer": forms.TextInput(attrs={"class": "form-control"}),
            "wrong_answers": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "theory_summary": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "practice_prompt": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "explanation": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "difficulty": forms.Select(attrs={"class": "form-select"}),
            "time_limit_seconds": forms.NumberInput(attrs={"class": "form-control"}),
            "points": forms.NumberInput(attrs={"class": "form-control"}),
            "bonus_time_threshold": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "display_name",
            "bio",
            "mascot_slug",
            "theme_slug",
            "favorite_subject",
            "xp",
            "level",
            "streak",
            "weekly_goal",
            "notifications_enabled",
            "parent_email",
            "learning_goal",
            "preferred_locale",
        ]
        widgets = {
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"rows": 3}),
            "mascot_slug": forms.TextInput(attrs={"class": "form-control"}),
            "theme_slug": forms.TextInput(attrs={"class": "form-control"}),
            "favorite_subject": forms.Select(attrs={"class": "form-select"}),
            "xp": forms.NumberInput(attrs={"class": "form-control"}),
            "level": forms.NumberInput(attrs={"class": "form-control"}),
            "streak": forms.NumberInput(attrs={"class": "form-control"}),
            "weekly_goal": forms.NumberInput(attrs={"class": "form-control"}),
            "notifications_enabled": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "parent_email": forms.EmailInput(attrs={"class": "form-control"}),
            "learning_goal": forms.Select(attrs={"class": "form-select"}),
            "preferred_locale": forms.TextInput(attrs={"class": "form-control"}),
        }


class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "description", "team_support"]


class ClassAssignmentForm(forms.ModelForm):
    class Meta:
        model = ClassAssignment
        fields = ["title", "description", "due_date", "points"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


class ThreadForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        help_text="Separă tag-urile cu virgulă",
    )

    class Meta:
        model = CommunityThread
        fields = ["title", "body"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }


class ReplyForm(forms.ModelForm):
    class Meta:
        model = CommunityReply
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class ProjectSubmissionForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={"rows": 4}))
    solution_url = forms.URLField(required=False)
    attachment = forms.FileField(required=False)

    class Meta:
        model = ProjectSubmission
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["description"].initial = self.instance.feedback

    def save(self, commit=True):
        submission = super().save(commit=False)
        description = (self.cleaned_data.get("description") or "").strip()
        solution_url = (self.cleaned_data.get("solution_url") or "").strip()
        attachment = self.cleaned_data.get("attachment")

        submission.feedback = description

        checklist = submission.pre_submit_checklist
        if not isinstance(checklist, list):
            checklist = []
        checklist = [
            item
            for item in checklist
            if not (isinstance(item, dict) and item.get("type") == "submission_meta")
        ]

        submission_meta = {"type": "submission_meta"}
        if solution_url:
            submission_meta["solution_url"] = solution_url
        if attachment:
            submission_meta["attachment_name"] = attachment.name
        if len(submission_meta) > 1:
            checklist.append(submission_meta)

        submission.pre_submit_checklist = checklist

        if commit:
            submission.save()
        return submission


class NotificationPreferenceForm(forms.ModelForm):
    class Meta:
        model = NotificationPreference
        fields = ["email_enabled", "in_app_enabled", "digest_frequency"]
