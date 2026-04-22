from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase

from .models import UserProfile
from .services.permissions import (
    ACTION_ANALYTICS_VIEW,
    ACTION_CLASSROOM_MANAGE,
    ACTION_DASHBOARD_ADMIN,
    ACTION_DASHBOARD_PARENT,
    ACTION_DASHBOARD_STUDENT,
    ACTION_DASHBOARD_TEACHER,
    ACTION_MODERATE_COMMENTS,
    ROLE_ADMIN,
    ROLE_PARENT,
    ROLE_STUDENT,
    ROLE_TEACHER,
    get_user_role,
    is_allowed,
)


class PermissionMatrixTests(TestCase):
    def _create_user(self, username: str, role: str):
        user = User.objects.create_user(username=username, password="pass1234")
        profile = user.userprofile
        profile.status = role
        profile.save(update_fields=["status"])
        return user

    def test_student_permissions(self):
        user = self._create_user("student", ROLE_STUDENT)

        self.assertTrue(is_allowed(user, ACTION_DASHBOARD_STUDENT))
        self.assertFalse(is_allowed(user, ACTION_DASHBOARD_TEACHER))
        self.assertFalse(is_allowed(user, ACTION_DASHBOARD_ADMIN))
        self.assertFalse(is_allowed(user, ACTION_DASHBOARD_PARENT))

    def test_teacher_permissions(self):
        user = self._create_user("teacher", ROLE_TEACHER)

        self.assertTrue(is_allowed(user, ACTION_DASHBOARD_TEACHER))
        self.assertTrue(is_allowed(user, ACTION_CLASSROOM_MANAGE))
        self.assertTrue(is_allowed(user, ACTION_MODERATE_COMMENTS))
        self.assertTrue(is_allowed(user, ACTION_ANALYTICS_VIEW))
        self.assertFalse(is_allowed(user, ACTION_DASHBOARD_ADMIN))

    def test_parent_permissions(self):
        user = self._create_user("parent", ROLE_PARENT)

        self.assertTrue(is_allowed(user, ACTION_DASHBOARD_PARENT))
        self.assertFalse(is_allowed(user, ACTION_CLASSROOM_MANAGE))
        self.assertFalse(is_allowed(user, ACTION_ANALYTICS_VIEW))

    def test_admin_permissions(self):
        user = self._create_user("admin", ROLE_ADMIN)

        self.assertTrue(is_allowed(user, ACTION_DASHBOARD_ADMIN))
        self.assertTrue(is_allowed(user, ACTION_ANALYTICS_VIEW))
        self.assertFalse(is_allowed(user, ACTION_CLASSROOM_MANAGE))

    def test_unknown_action_denied(self):
        user = self._create_user("student2", ROLE_STUDENT)

        self.assertFalse(is_allowed(user, "unknown.action"))

    def test_missing_profile_denied(self):
        user = User.objects.create_user(username="no-profile", password="pass1234")
        UserProfile.objects.filter(user=user).delete()

        self.assertFalse(is_allowed(user, ACTION_DASHBOARD_STUDENT))

    def test_anonymous_user_denied(self):
        anonymous = AnonymousUser()

        self.assertIsNone(get_user_role(anonymous))
        self.assertFalse(is_allowed(anonymous, ACTION_DASHBOARD_STUDENT))
