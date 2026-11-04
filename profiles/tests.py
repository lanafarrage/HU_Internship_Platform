import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Skill, StudentProfile, StudentSkill

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("lana", password="pass12345")
        self.client.force_authenticate(self.user)

    def test_create_and_edit_profile(self):
        r = self.client.patch("/api/profile/me/", {"full_name": "Lana F"}, format="json")
        self.assertEqual(r.status_code, 200)
        r = self.client.get("/api/profile/me/")
        self.assertEqual(r.data["full_name"], "Lana F")

    def test_cv_upload_and_replace(self):
        first = SimpleUploadedFile("a.pdf", b"%PDF-1", content_type="application/pdf")
        self.client.patch("/api/profile/me/", {"cv": first}, format="multipart")
        old_path = StudentProfile.objects.get(user=self.user).cv.path
        self.assertTrue(os.path.exists(old_path))

        second = SimpleUploadedFile("b.pdf", b"%PDF-2", content_type="application/pdf")
        r = self.client.patch("/api/profile/me/", {"cv": second}, format="multipart")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(os.path.exists(old_path))  # old file removed

    def test_rejects_wrong_cv_type(self):
        bad = SimpleUploadedFile("a.txt", b"hello", content_type="text/plain")
        r = self.client.patch("/api/profile/me/", {"cv": bad}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_skills_add_update_remove(self):
        skill = Skill.objects.create(name="Python")
        r = self.client.post(
            "/api/profile/me/skills/", {"skill": skill.id, "level": "beginner"}, format="json"
        )
        self.assertEqual(r.status_code, 201)
        sid = r.data["id"]

        r = self.client.patch(f"/api/profile/me/skills/{sid}/", {"level": "advanced"}, format="json")
        self.assertEqual(r.data["level"], "advanced")

        r = self.client.post("/api/profile/me/skills/", {"skill": skill.id}, format="json")
        self.assertEqual(r.status_code, 400)  # duplicate rejected

        self.assertEqual(self.client.delete(f"/api/profile/me/skills/{sid}/").status_code, 204)
        r = self.client.get("/api/profile/me/")
        self.assertEqual(r.data["student_skills"], [])

    def test_cannot_touch_another_students_skill(self):
        other = User.objects.create_user("sara", password="pass12345")
        other_profile = StudentProfile.objects.create(user=other, full_name="Sara")
        skill = Skill.objects.create(name="SQL")
        ss = StudentSkill.objects.create(profile=other_profile, skill=skill)
        r = self.client.delete(f"/api/profile/me/skills/{ss.id}/")
        self.assertEqual(r.status_code, 404)
