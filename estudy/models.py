from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


def default_theory_takeaways():
    return []


class Lesson(models.Model):
    DIFFICULTY_BEGINNER = "beginner"
    DIFFICULTY_INTERMEDIATE = "intermediate"
    DIFFICULTY_ADVANCED = "advanced"

    DIFFICULTY_CHOICES = [
        (DIFFICULTY_BEGINNER, "Beginner"),
        (DIFFICULTY_INTERMEDIATE, "Intermediate"),
        (DIFFICULTY_ADVANCED, "Advanced"),
    ]

    AGE_8_10 = "8-10"
    AGE_11_13 = "11-13"
    AGE_14_16 = "14-16"
    AGE_16_PLUS = "16+"

    AGE_BRACKET_CHOICES = [
        (AGE_8_10, _("8-10 ani")),
        (AGE_11_13, _("11-13 ani")),
        (AGE_14_16, _("14-16 ani")),
        (AGE_16_PLUS, _("16+ ani")),
    ]

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True, null=True)
    excerpt = models.CharField(max_length=300, blank=True)
    content = models.TextField()
    date = models.DateField()
    duration_minutes = models.PositiveIntegerField(default=45)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default=DIFFICULTY_BEGINNER)
    cover_image = models.ImageField(upload_to="lessons/covers/", blank=True, null=True)
    age_bracket = models.CharField(max_length=20, choices=AGE_BRACKET_CHOICES, default=AGE_11_13)
    theory_intro = models.TextField(blank=True)
    theory_takeaways = models.JSONField(default=default_theory_takeaways, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ("date", "title")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "lesson"
            slug = base_slug
            index = 1
            while Lesson.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                index += 1
                slug = f"{base_slug}-{index}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_resources_as_list(self) -> list[str]:
        """Return resource URLs for legacy template usage."""
        return [resource.url for resource in self.materials.all()]

    def get_absolute_url(self) -> str:
        return reverse("lesson_detail", args=[self.slug])

    @property
    def is_upcoming(self) -> bool:
        return self.date >= timezone.localdate()

    @property
    def difficulty_label(self) -> str:
        return dict(self.DIFFICULTY_CHOICES).get(self.difficulty, self.difficulty)

    @property
    def age_label(self) -> str:
        return dict(self.AGE_BRACKET_CHOICES).get(self.age_bracket, self.age_bracket)

    def theory_points(self) -> list[str]:
        return [item for item in self.theory_takeaways if isinstance(item, str) and item.strip()]

    def difficulty_palette(self) -> dict[str, str]:
        return {
            "beginner": {
                "bg": "linear-gradient(135deg, #34d399, #10b981)",
                "accent": "#047857",
                "emoji": "🌱",
            },
            "intermediate": {
                "bg": "linear-gradient(135deg, #60a5fa, #2563eb)",
                "accent": "#1e3a8a",
                "emoji": "🚀",
            },
            "advanced": {
                "bg": "linear-gradient(135deg, #f59e0b, #f97316)",
                "accent": "#b45309",
                "emoji": "🧠",
            },
        }.get(self.difficulty, {
            "bg": "linear-gradient(135deg, #818cf8, #4f46e5)",
            "accent": "#312e81",
            "emoji": "✨",
        })

    def __str__(self) -> str:
        return self.title


class LessonResource(models.Model):
    TYPE_ARTICLE = "article"
    TYPE_VIDEO = "video"
    TYPE_WORKSHEET = "worksheet"
    TYPE_INTERACTIVE = "interactive"

    RESOURCE_TYPE_CHOICES = [
        (TYPE_ARTICLE, "Article"),
        (TYPE_VIDEO, "Video"),
        (TYPE_WORKSHEET, "Worksheet"),
        (TYPE_INTERACTIVE, "Interactive"),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=150)
    url = models.URLField()
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES, default=TYPE_ARTICLE)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")

    def __str__(self) -> str:
        return f"{self.lesson.title} · {self.title}"


class UserProfile(models.Model):
    STATUS_CHOICES = [
        ("student", "Student"),
        ("admin", "Admin"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="student")

    def __str__(self) -> str:
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.userprofile.save()


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_records")
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("user", "lesson")

    def __str__(self) -> str:
        status = "Completed" if self.completed else "In progress"
        return f"{self.user.username} · {self.lesson.title} · {status}"

    def mark_completed(self) -> None:
        self.completed = True
        if not self.completed_at:
            self.completed_at = timezone.now()
        self.save(update_fields=["completed", "completed_at", "updated_at"])

    def toggle(self) -> None:
        self.completed = not self.completed
        self.completed_at = timezone.now() if self.completed else None
        self.save(update_fields=["completed", "completed_at", "updated_at"])


class Reward(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to="rewards/", blank=True, null=True)

    def __str__(self) -> str:
        return self.name


class UserReward(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rewards")
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    date_awarded = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user.username} · {self.reward.name}"


def check_and_award_rewards(user: User) -> None:
    completed_lessons = LessonProgress.objects.filter(user=user, completed=True).count()
    if completed_lessons >= 10:
        reward, _ = Reward.objects.get_or_create(
            name="10 Lessons Complete",
            defaults={"description": "Completed ten lessons."},
        )
        UserReward.objects.get_or_create(user=user, reward=reward)


class Test(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="tests")
    question = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=255)
    wrong_answers = models.JSONField()
    theory_summary = models.TextField(blank=True)
    practice_prompt = models.TextField(blank=True)
    explanation = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.question

    def answer_choices(self) -> list[str]:
        return [self.correct_answer, *self.wrong_answers]


class TestAttempt(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="test_attempts")
    selected_answer = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.user.username} · {self.test.question[:30]}..."


def default_practice_data() -> dict[str, list]:
    return {"draggables": [], "targets": []}


class LessonPractice(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name="practice")
    intro = models.TextField(blank=True)
    instructions = models.CharField(max_length=200, blank=True)
    success_message = models.CharField(max_length=150, default="Super! Ai reușit să potrivești corect.")
    data = models.JSONField(default=default_practice_data, blank=True)

    def __str__(self) -> str:
        return f"Practice · {self.lesson.title}"

    @property
    def has_pairs(self) -> bool:
        draggables = self.data.get("draggables", []) if isinstance(self.data, dict) else []
        targets = self.data.get("targets", []) if isinstance(self.data, dict) else []
        return bool(draggables and targets)
