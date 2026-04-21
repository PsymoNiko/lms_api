from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class CurrentUserMeViewTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="stu",
            email="stu@example.com",
            password="pass12345",
            role="student",
        )
        self.instructor = User.objects.create_user(
            username="ins",
            email="ins@example.com",
            password="pass12345",
            role="instructor",
            is_staff=True,
        )
        self.admin = User.objects.create_user(
            username="adm",
            email="adm@example.com",
            password="pass12345",
            role="admin",
            is_staff=True,
        )

    def test_me_requires_auth(self):
        r = self.client.get("/api/v1/me/")
        self.assertEqual(r.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_student_flags(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.get("/api/v1/me/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["role"], "student")
        self.assertTrue(r.data["access"]["can_enroll_in_courses"])
        self.assertFalse(r.data["access"]["can_write_courses"])
        self.assertFalse(r.data["access"]["can_manage_users"])

    def test_me_instructor_flags(self):
        self.client.force_authenticate(user=self.instructor)
        r = self.client.get("/api/v1/me/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["role"], "instructor")
        self.assertTrue(r.data["access"]["can_write_courses"])
        self.assertTrue(r.data["access"]["can_use_mine_courses_query"])
        self.assertFalse(r.data["access"]["can_manage_users"])
        self.assertTrue(r.data["access"]["can_access_django_admin"])

    def test_me_admin_flags(self):
        self.client.force_authenticate(user=self.admin)
        r = self.client.get("/api/v1/me/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertEqual(r.data["role"], "admin")
        self.assertTrue(r.data["access"]["can_manage_users"])
        self.assertTrue(r.data["access"]["can_access_site_owner_panel"])


class SiteAdminOverviewViewTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="stu2",
            email="stu2@example.com",
            password="pass12345",
            role="student",
        )
        self.admin = User.objects.create_user(
            username="adm2",
            email="adm2@example.com",
            password="pass12345",
            role="admin",
            is_staff=True,
        )

    def test_overview_forbidden_for_student(self):
        self.client.force_authenticate(user=self.student)
        r = self.client.get("/api/v1/admin/overview/")
        self.assertEqual(r.status_code, status.HTTP_403_FORBIDDEN)

    def test_overview_ok_for_platform_admin(self):
        self.client.force_authenticate(user=self.admin)
        r = self.client.get("/api/v1/admin/overview/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        self.assertIn("counts", r.data)
        self.assertIn("recent", r.data)
        self.assertIn("users", r.data["counts"])
        self.assertIn("users_by_role", r.data["counts"])
