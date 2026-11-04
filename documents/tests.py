from django.test import TestCase

# Create your tests here.
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Document, Placement

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class DocumentTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user("student1", password="pass12345")
        self.other = User.objects.create_user("student2", password="pass12345")
        self.reviewer = User.objects.create_user(
            "coordinator", password="pass12345", is_staff=True
        )
        self.placement = Placement.objects.create(
            student=self.student, company_name="Acme", title="Intern"
        )
        self.other_placement = Placement.objects.create(
            student=self.other, company_name="Beta", title="Intern"
        )

    def pdf(self, name="cv.pdf"):
        return SimpleUploadedFile(name, b"%PDF-1", content_type="application/pdf")

    def upload(self, placement):
        return self.client.post(
            "/api/documents/",
            {"placement": placement.id, "document_type": "offer_letter", "file": self.pdf()},
            format="multipart",
        )

    def test_student_can_upload(self):
        self.client.force_authenticate(self.student)
        r = self.upload(self.placement)
        self.assertEqual(r.status_code, 201)

    def test_linked_to_correct_student_and_placement(self):
        self.client.force_authenticate(self.student)
        r = self.upload(self.placement)
        doc = Document.objects.get(id=r.data["id"])
        self.assertEqual(doc.uploaded_by, self.student)
        self.assertEqual(doc.placement, self.placement)

    def test_cannot_upload_to_another_students_placement(self):
        self.client.force_authenticate(self.student)
        r = self.upload(self.other_placement)
        self.assertEqual(r.status_code, 400)

    def test_wrong_file_type_fails(self):
        self.client.force_authenticate(self.student)
        bad = SimpleUploadedFile("a.txt", b"hello", content_type="text/plain")
        r = self.client.post(
            "/api/documents/",
            {"placement": self.placement.id, "document_type": "other", "file": bad},
            format="multipart",
        )
        self.assertEqual(r.status_code, 400)

    def test_reviewer_can_see_all_students_cannot(self):
        self.client.force_authenticate(self.student)
        r = self.upload(self.placement)
        doc_id = r.data["id"]

        self.client.force_authenticate(self.reviewer)
        self.assertEqual(self.client.get(f"/api/documents/{doc_id}/").status_code, 200)

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/documents/{doc_id}/").status_code, 404)