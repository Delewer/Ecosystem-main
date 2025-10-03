import secrets
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from typing import Optional





def default_empty_list():
    return []


def default_empty_dict():
    return {}


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
    xp_reward = models.PositiveIntegerField(default=50, validators=[MinValueValidator(0), MaxValueValidator(500)])
    fun_fact = models.TextField(blank=True)
    featured = models.BooleanField(default=False)
    hero_theme = models.CharField(max_length=60, default="sky-fizz")
    hero_emoji = models.CharField(max_length=10, default="🚀")

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
    ROLE_STUDENT = "student"
    ROLE_PROFESSOR = "professor"
    ROLE_ADMIN = "admin"
    ROLE_PARENT = "parent"

    STATUS_CHOICES = [
        (ROLE_STUDENT, "Student"),
        (ROLE_PROFESSOR, "Profesor"),
        (ROLE_ADMIN, "Administrator"),
        (ROLE_PARENT, "Parinte"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ROLE_STUDENT)

    display_name = models.CharField(max_length=120, blank=True)
    bio = models.TextField(blank=True)
    mascot_slug = models.CharField(max_length=40, default="robo-fox")
    theme_slug = models.CharField(max_length=40, default="sunny")
    favorite_subject = models.ForeignKey('Subject', on_delete=models.SET_NULL, blank=True, null=True, related_name='fans')
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    streak = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField(blank=True, null=True)
    weekly_goal = models.PositiveIntegerField(default=3)
    notifications_enabled = models.BooleanField(default=True)
    parent_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self) -> str:
        return self.user.username


    def role_label(self) -> str:
        return dict(self.STATUS_CHOICES).get(self.status, self.status)

    def is_student(self) -> bool:
        return self.status == self.ROLE_STUDENT

    def is_teacher(self) -> bool:
        return self.status == self.ROLE_PROFESSOR

    def is_admin(self) -> bool:
        return self.status == self.ROLE_ADMIN

    def is_parent(self) -> bool:
        return self.status == self.ROLE_PARENT

    def display_or_username(self) -> str:
        return self.display_name or self.user.get_short_name() or self.user.username


    def next_level_xp(self) -> int:
        return 100 + (self.level ** 2) * 25

    def add_xp(self, amount: int, reason: str = "") -> None:
        if amount <= 0:
            return
        self.xp += amount
        leveled_up = False
        while self.xp >= self.next_level_xp():
            self.level += 1
            leveled_up = True
        self.last_activity_at = timezone.now()
        self.save(update_fields=["xp", "level", "last_activity_at"])
        ExperienceLog.objects.create(user=self.user, amount=amount, reason=reason or "XP update")
        if leveled_up:
            Notification.objects.create(
                recipient=self.user,
                title="Yay! Ai urcat de nivel",
                message=f"Bravo! Acum esti la nivelul {self.level}. Continua aventura.",
                category=Notification.CATEGORY_PROGRESS,
            )

    def progress_to_next_level(self) -> float:
        previous_threshold = 100 + ((self.level - 1) ** 2) * 25
        target = self.next_level_xp()
        if target <= previous_threshold:
            return 0.0
        return max(0.0, min(100.0, ((self.xp - previous_threshold) / (target - previous_threshold)) * 100))


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)
        NotificationPreference.objects.get_or_create(user=instance)
        return profile
    instance.userprofile.save()


class ExperienceLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="xp_logs")
    amount = models.IntegerField()
    reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    time_taken_ms = models.PositiveIntegerField(default=0)
    awarded_points = models.PositiveIntegerField(default=0)
    earned_bonus = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.user.username} +{self.amount} XP"


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_records")
    completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    points_earned = models.PositiveIntegerField(default=0)
    fastest_completion_seconds = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "lesson")

    def __str__(self) -> str:
        status = "Completed" if self.completed else "In progress"
        return f"{self.user.username} · {self.lesson.title} · {status}"

    def mark_completed(self, *, seconds_spent: Optional[int] = None, award_xp: bool = True) -> None:
        already_completed = self.completed
        if not already_completed:
            self.completed = True
        if not self.completed_at:
            self.completed_at = timezone.now()
        update_fields = ["completed", "completed_at", "updated_at"]
        if seconds_spent is not None:
            if self.fastest_completion_seconds == 0 or seconds_spent < self.fastest_completion_seconds:
                self.fastest_completion_seconds = seconds_spent
                update_fields.append("fastest_completion_seconds")
        xp_awarded = 0
        if award_xp and not already_completed and hasattr(self.user, "userprofile"):
            xp_awarded = self.lesson.xp_reward
            self.user.userprofile.add_xp(xp_awarded, reason=f"Lesson {self.lesson.title} completed")
        if xp_awarded and xp_awarded > self.points_earned:
            self.points_earned = xp_awarded
            if "points_earned" not in update_fields:
                update_fields.append("points_earned")
        self.save(update_fields=update_fields)

    def toggle(self, award_xp: bool = True) -> None:
        self.completed = not self.completed
        if self.completed:
            self.mark_completed(award_xp=award_xp)
        else:
            self.completed_at = None
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


class Badge(models.Model):
    RULE_LESSONS = "lessons_completed"
    RULE_STREAK = "quiz_streak"
    RULE_SPEED = "fast_finisher"
    RULE_PROJECT = "project_submitted"
    RULE_CHALLENGE = "challenge_master"

    RULE_CHOICES = [
        (RULE_LESSONS, "Lessons completed"),
        (RULE_STREAK, "Quiz streak"),
        (RULE_SPEED, "Fast finisher"),
        (RULE_PROJECT, "Project submitted"),
        (RULE_CHALLENGE, "Challenge master"),
    ]

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=40, default="fa-star")
    color = models.CharField(max_length=20, default="#2563eb")
    rule = models.CharField(max_length=40, choices=RULE_CHOICES, blank=True)
    threshold = models.PositiveIntegerField(default=0)
    xp_reward = models.PositiveIntegerField(default=50)
    is_secret = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    time_taken_ms = models.PositiveIntegerField(default=0)
    awarded_points = models.PositiveIntegerField(default=0)
    earned_bonus = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="badge_awards")
    badge = models.ForeignKey('Badge', on_delete=models.CASCADE, related_name="awards")
    awarded_at = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=60, blank=True)

    class Meta:
        unique_together = ("user", "badge")
        ordering = ("-awarded_at",)

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.badge.name}"


class Mission(models.Model):
    FREQ_DAILY = "daily"
    FREQ_WEEKLY = "weekly"
    FREQ_ONCE = "once"

    FREQUENCY_CHOICES = [
        (FREQ_DAILY, "Daily"),
        (FREQ_WEEKLY, "Weekly"),
        (FREQ_ONCE, "One time"),
    ]

    code = models.SlugField(unique=True)
    title = models.CharField(max_length=150)
    description = models.TextField()
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default=FREQ_DAILY)
    target_value = models.PositiveIntegerField(default=1)
    reward_points = models.PositiveIntegerField(default=50)
    reward_badge = models.ForeignKey('Badge', on_delete=models.SET_NULL, blank=True, null=True)
    icon = models.CharField(max_length=40, default="fa-rocket")
    color = models.CharField(max_length=20, default="#6366f1")
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.title


class UserMission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="missions")
    mission = models.ForeignKey('Mission', on_delete=models.CASCADE, related_name="states")
    progress = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_reset = models.DateField(blank=True, null=True)

    class Meta:
        unique_together = ("user", "mission")

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.mission.code}"

    def register_progress(self, value: int = 1) -> None:
        today = timezone.localdate()
        if self.mission.frequency == Mission.FREQ_DAILY and self.last_reset != today:
            self.progress = 0
        elif self.mission.frequency == Mission.FREQ_WEEKLY and self.last_reset and self.last_reset.isocalendar() != today.isocalendar():
            self.progress = 0
        self.progress += value
        self.last_reset = today
        if not self.completed and self.progress >= self.mission.target_value:
            self.completed = True
            self.completed_at = timezone.now()
            if hasattr(self.user, "userprofile"):
                self.user.userprofile.add_xp(self.mission.reward_points, reason=f"Mission {self.mission.title}")
            if self.mission.reward_badge_id:
                UserBadge.objects.get_or_create(
                    user=self.user,
                    badge=self.mission.reward_badge,
                    defaults={"reason": f"Mission {self.mission.title} completed"},
                )
        self.save()


class NotificationPreference(models.Model):
    DIGEST_DAILY = "daily"
    DIGEST_WEEKLY = "weekly"
    DIGEST_NEVER = "never"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notification_preferences")
    email_enabled = models.BooleanField(default=False)
    in_app_enabled = models.BooleanField(default=True)
    digest_frequency = models.CharField(max_length=20, choices=[(DIGEST_DAILY, "Daily"), (DIGEST_WEEKLY, "Weekly"), (DIGEST_NEVER, "Never")], default=DIGEST_WEEKLY)

    def __str__(self) -> str:
        return f"Preferences for {self.user.username}"


class Notification(models.Model):
    CATEGORY_PROGRESS = "progress"
    CATEGORY_FEEDBACK = "feedback"
    CATEGORY_SYSTEM = "system"
    CATEGORY_COMMUNITY = "community"

    CATEGORY_CHOICES = [
        (CATEGORY_PROGRESS, "Progress"),
        (CATEGORY_FEEDBACK, "Feedback"),
        (CATEGORY_SYSTEM, "System"),
        (CATEGORY_COMMUNITY, "Community"),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=120)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default=CATEGORY_SYSTEM)
    link_url = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Notification for {self.recipient.username}: {self.title}"

    def mark_as_read(self) -> None:
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])


class Classroom(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_classrooms")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    invite_code = models.CharField(max_length=12, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    archived = models.BooleanField(default=False)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.invite_code:
            code = secrets.token_hex(3).upper()
            while Classroom.objects.filter(invite_code=code).exists():
                code = secrets.token_hex(3).upper()
            self.invite_code = code
        super().save(*args, **kwargs)


class ClassroomMembership(models.Model):
    ROLE_STUDENT = "student"
    ROLE_ASSISTANT = "assistant"

    ROLE_CHOICES = [
        (ROLE_STUDENT, "Student"),
        (ROLE_ASSISTANT, "Assistant"),
    ]

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="classroom_memberships")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    joined_at = models.DateTimeField(auto_now_add=True)
    points = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("classroom", "user")

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.classroom.name}"


class ClassAssignment(models.Model):
    TYPE_LESSON = "lesson"
    TYPE_PROJECT = "project"
    TYPE_CUSTOM = "custom"

    TYPE_CHOICES = [
        (TYPE_LESSON, "Lesson"),
        (TYPE_PROJECT, "Project"),
        (TYPE_CUSTOM, "Custom"),
    ]

    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="assignments")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_assignments")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    assignment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_LESSON)
    lesson = models.ForeignKey('Lesson', on_delete=models.SET_NULL, blank=True, null=True)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    points = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    time_taken_ms = models.PositiveIntegerField(default=0)
    awarded_points = models.PositiveIntegerField(default=0)
    earned_bonus = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    def __str__(self) -> str:
        return f"{self.title} -> {self.classroom.name}"


class AssignmentSubmission(models.Model):
    STATUS_SUBMITTED = "submitted"
    STATUS_REVIEWED = "reviewed"
    STATUS_RETURNED = "returned"

    STATUS_CHOICES = [
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_RETURNED, "Returned"),
    ]

    assignment = models.ForeignKey('ClassAssignment', on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assignment_submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(blank=True)
    attachment = models.FileField(upload_to="assignments/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    feedback = models.TextField(blank=True)
    score = models.PositiveIntegerField(blank=True, null=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="assignment_reviews")

    class Meta:
        unique_together = ("assignment", "student")
        ordering = ("-submitted_at",)

    def __str__(self) -> str:
        return f"{self.assignment.title} -> {self.student.username}"


class Project(models.Model):
    LEVEL_BEGINNER = "beginner"
    LEVEL_INTERMEDIATE = "intermediate"
    LEVEL_ADVANCED = "advanced"

    LEVEL_CHOICES = [
        (LEVEL_BEGINNER, "Beginner"),
        (LEVEL_INTERMEDIATE, "Intermediate"),
        (LEVEL_ADVANCED, "Advanced"),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.CharField(max_length=250)
    brief = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default=LEVEL_BEGINNER)
    estimated_minutes = models.PositiveIntegerField(default=90)
    points_reward = models.PositiveIntegerField(default=150)
    lesson = models.ForeignKey('Lesson', on_delete=models.SET_NULL, blank=True, null=True, related_name="projects")
    skills = models.JSONField(default=default_empty_list, blank=True)
    resources = models.JSONField(default=default_empty_list, blank=True)
    rubric = models.JSONField(default=default_empty_dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    time_taken_ms = models.PositiveIntegerField(default=0)
    awarded_points = models.PositiveIntegerField(default=0)
    earned_bonus = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.title


class ProjectSubmission(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_NEEDS_WORK = "needs_work"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_NEEDS_WORK, "Needs updates"),
    ]

    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="project_submissions")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    solution_url = models.URLField(blank=True)
    attachment = models.FileField(upload_to="projects/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    feedback = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="project_reviews")
    score = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ("-uploaded_at",)

    def __str__(self) -> str:
        return f"{self.project.title} -> {self.student.username}"


class LearningPath(models.Model):
    title = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    theme = models.CharField(max_length=40, default="rainbow")
    difficulty = models.CharField(max_length=20, choices=Lesson.DIFFICULTY_CHOICES, default=Lesson.DIFFICULTY_BEGINNER)
    audience = models.CharField(max_length=60, default="general")
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    time_taken_ms = models.PositiveIntegerField(default=0)
    awarded_points = models.PositiveIntegerField(default=0)
    earned_bonus = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ("title",)

    def __str__(self) -> str:
        return self.title


class LearningPathLesson(models.Model):
    path = models.ForeignKey('LearningPath', on_delete=models.CASCADE, related_name="items")
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name="path_items")
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("order",)
        unique_together = ("path", "lesson")

    def __str__(self) -> str:
        return f"{self.path.title} -> {self.lesson.title}"


class LearningRecommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommendations")
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE)
    reason = models.CharField(max_length=255)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    consumed = models.BooleanField(default=False)

    class Meta:
        ordering = ("-score", "-created_at")
        unique_together = ("user", "lesson")

    def __str__(self) -> str:
        return f"Recommendation for {self.user.username}: {self.lesson.title}"


class ParentChildLink(models.Model):
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="children_links")
    child = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parent_links")
    created_at = models.DateTimeField(auto_now_add=True)

    time_taken_ms = models.PositiveIntegerField(default=0)
    awarded_points = models.PositiveIntegerField(default=0)
    earned_bonus = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

    class Meta:
        unique_together = ("parent", "child")

    def __str__(self) -> str:
        return f"{self.parent.username} -> {self.child.username}"


class CommunityThread(models.Model):
    title = models.CharField(max_length=200)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="threads")
    created_at = models.DateTimeField(auto_now_add=True)
    body = models.TextField()
    tags = models.JSONField(default=default_empty_list, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ("-is_pinned", "-created_at")

    def __str__(self) -> str:
        return self.title


class CommunityReply(models.Model):
    thread = models.ForeignKey('CommunityThread', on_delete=models.CASCADE, related_name="replies")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)
    body = models.TextField()
    is_flagged = models.BooleanField(default=False)

    class Meta:
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"Reply by {self.created_by.username}"


class DailyChallenge(models.Model):
    code = models.SlugField(unique=True)
    title = models.CharField(max_length=160)
    description = models.TextField()
    points = models.PositiveIntegerField(default=50)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        ordering = ("-start_date",)

    def __str__(self) -> str:
        return self.title


class ChallengeAttempt(models.Model):
    challenge = models.ForeignKey('DailyChallenge', on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="challenge_attempts")
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_successful = models.BooleanField(default=False)

    class Meta:
        unique_together = ("challenge", "user")

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.challenge.code}"


class AIHintRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_requests")
    lesson = models.ForeignKey('Lesson', on_delete=models.SET_NULL, blank=True, null=True)
    question = models.TextField()
    response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"AI request by {self.user.username}"


class AvatarUnlock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="avatar_unlocks")
    slug = models.CharField(max_length=60)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "slug")

    def __str__(self) -> str:
        return f"{self.user.username} unlocked {self.slug}"


class LeaderboardSnapshot(models.Model):
    PERIOD_WEEK = "week"
    PERIOD_MONTH = "month"

    period = models.CharField(max_length=10, choices=[(PERIOD_WEEK, "Week"), (PERIOD_MONTH, "Month")], default=PERIOD_WEEK)
    classroom = models.ForeignKey('Classroom', on_delete=models.CASCADE, blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(default=default_empty_list, blank=True)

    class Meta:
        ordering = ("-generated_at",)

    def __str__(self) -> str:
        scope = self.classroom.name if self.classroom else "global"
        return f"Leaderboard {scope} {self.period}"




def check_and_award_rewards(user: User) -> None:
    completed_lessons = LessonProgress.objects.filter(user=user, completed=True).count()
    profile = getattr(user, "userprofile", None)

    milestones = [
        ("curious-coder", 3, "Curious Coder", "fa-lightbulb", "#22c55e"),
        ("fast-learner", 5, "Fast Learner", "fa-bolt", "#f97316"),
        ("lesson-explorer", 10, "Lesson Explorer", "fa-map", "#6366f1"),
        ("learning-legend", 20, "Learning Legend", "fa-crown", "#a855f7"),
    ]

    for slug, threshold, name, icon, color in milestones:
        if completed_lessons < threshold:
            continue
        badge, _ = Badge.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "description": f"Completed {threshold} lessons",
                "icon": icon,
                "color": color,
                "rule": Badge.RULE_LESSONS,
                "threshold": threshold,
                "xp_reward": 40 + threshold * 4,
            },
        )
        award, created = UserBadge.objects.get_or_create(
            user=user,
            badge=badge,
            defaults={"reason": f"Completed {threshold} lessons"},
        )
        if created:
            if profile:
                profile.add_xp(badge.xp_reward, reason=f"Badge {badge.name}")
            Notification.objects.create(
                recipient=user,
                title=f"Ai castigat insigna {badge.name}!",
                message=f"Tine-o tot asa, ai atins pragul de {threshold} lectii.",
                category=Notification.CATEGORY_PROGRESS,
            )

    if completed_lessons >= 10:
        reward, _ = Reward.objects.get_or_create(
            name="10 Lessons Complete",
            defaults={"description": "Completed ten lessons."},
        )
        UserReward.objects.get_or_create(user=user, reward=reward)

    if profile:
        profile.streak += 1
        profile.last_activity_at = timezone.now()
        profile.save(update_fields=["streak", "last_activity_at"])



class Test(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="tests")
    question = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=255)
    wrong_answers = models.JSONField()
    theory_summary = models.TextField(blank=True)
    practice_prompt = models.TextField(blank=True)
    explanation = models.TextField(blank=True)

    difficulty = models.CharField(max_length=20, choices=Lesson.DIFFICULTY_CHOICES, default=Lesson.DIFFICULTY_BEGINNER)
    time_limit_seconds = models.PositiveIntegerField(default=60)
    points = models.PositiveIntegerField(default=100)
    bonus_time_threshold = models.PositiveIntegerField(default=20)

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

    time_taken_ms = models.PositiveIntegerField(default=0)
    awarded_points = models.PositiveIntegerField(default=0)
    earned_bonus = models.BooleanField(default=False)
    feedback = models.TextField(blank=True)

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
