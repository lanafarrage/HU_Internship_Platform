from django.test import TestCase

# Create your tests here.
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Internship

User = get_user_model()


class InternshipTests(TestCase):
    def setUp(self):
        self.rep = User.objects.create_user(
            "rep1", "rep1@x.com", "pass12345", role="company_rep", company_name="Acme"
        )
        self.other_rep = User.objects.create_user(
            "rep2", "rep2@x.com", "pass12345", role="company_rep", company_name="Beta"
        )
        self.student = User.objects.create_user(
            "stu", "stu@x.com", "pass12345", role="student"
        )
        self.data = {
            "title": "Backend Intern",
            "description": "Build APIs",
            "required_skills": "Python, Django",
            "deadline": (date.today() + timedelta(days=30)).isoformat(),
            "location": "Beirut",
            "duration": "3 months",
        }

    def make(self, owner, **kw):
        return Internship.objects.create(
            company=owner,
            title=kw.get("title", "Existing"),
            description="d",
            required_skills="s",
            deadline=date.today() + timedelta(days=10),
            location="Beirut",
        )

    def test_rep_can_create_listing_owned_by_them(self):
        self.client.force_login(self.rep)
        r = self.client.post(reverse("dashboards:internship_create"), self.data)
        self.assertEqual(r.status_code, 302)
        item = Internship.objects.get(title="Backend Intern")
        self.assertEqual(item.company, self.rep)
        self.assertEqual(item.duration, "3 months")

    def test_student_cannot_create(self):
        self.client.force_login(self.student)
        self.client.post(reverse("dashboards:internship_create"), self.data)
        self.assertFalse(Internship.objects.filter(title="Backend Intern").exists())

    def test_rep_can_edit_own_listing(self):
        item = self.make(self.rep)
        self.client.force_login(self.rep)
        self.data["title"] = "Renamed"
        self.client.post(reverse("dashboards:internship_edit", args=[item.pk]), self.data)
        item.refresh_from_db()
        self.assertEqual(item.title, "Renamed")

    def test_rep_cannot_edit_or_close_another_reps_listing(self):
        item = self.make(self.other_rep)
        self.client.force_login(self.rep)
        r = self.client.post(reverse("dashboards:internship_edit", args=[item.pk]), self.data)
        self.assertEqual(r.status_code, 404)
        r = self.client.post(reverse("dashboards:internship_close", args=[item.pk]))
        self.assertEqual(r.status_code, 404)
        item.refresh_from_db()
        self.assertTrue(item.is_open)

    def test_close_hides_listing_from_open_list(self):
        item = self.make(self.rep)
        self.client.force_login(self.rep)
        self.client.post(reverse("dashboards:internship_close", args=[item.pk]))
        item.refresh_from_db()
        self.assertFalse(item.is_open)
        self.assertNotIn(item, Internship.objects.filter(is_open=True))

    def test_close_requires_post(self):
        item = self.make(self.rep)
        self.client.force_login(self.rep)
        r = self.client.get(reverse("dashboards:internship_close", args=[item.pk]))
        self.assertEqual(r.status_code, 405)

    def test_dashboard_shows_only_own_listings(self):
        self.make(self.rep, title="Mine")
        self.make(self.other_rep, title="Theirs")
        self.client.force_login(self.rep)
        r = self.client.get(reverse("dashboards:company"))
        self.assertContains(r, "Mine")
        self.assertNotContains(r, "Theirs")


class StudentVisibilityTests(TestCase):
    def setUp(self):
        self.rep = User.objects.create_user(
            "rep9", "rep9@x.com", "pass12345", role="company_rep", company_name="Acme")
        self.student = User.objects.create_user(
            "2510001", "s@students.haigazian.edu.lb", "pass12345", role="student")

    def make(self, title, **kw):
        return Internship.objects.create(
            company=self.rep, title=title, description="d", required_skills="s",
            deadline=kw.get("deadline", date.today() + timedelta(days=10)),
            location="Beirut", is_open=kw.get("is_open", True))

    def test_student_sees_open_but_not_closed_or_expired(self):
        self.make("OpenOne")
        self.make("ClosedOne", is_open=False)
        self.make("ExpiredOne", deadline=date.today() - timedelta(days=1))
        self.client.force_login(self.student)
        r = self.client.get(reverse("dashboards:student"))
        self.assertContains(r, "OpenOne")
        self.assertNotContains(r, "ClosedOne")
        self.assertNotContains(r, "ExpiredOne")

    def test_student_can_log_in_with_id_or_email(self):
        for ident in ("2510001", "s@students.haigazian.edu.lb"):
            self.client.logout()
            r = self.client.post(reverse("accounts:login"),
                                 {"username": ident, "password": "pass12345"})
            self.assertEqual(r.status_code, 302, ident)
