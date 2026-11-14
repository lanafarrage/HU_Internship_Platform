from django.test import TestCase
from django.urls import reverse

from .models import User

PASSWORD = "StrongPassword123!"  # used for all test users


def signup_data(**extra):
    data = {
        "username": "2510052",
        "first_name": "Sara",
        "last_name": "Ali",
        "email": "sara@haigazian.edu.lb",
        "password1": PASSWORD,
        "password2": PASSWORD,
    }
    data.update(extra)
    return data


class RegistrationTests(TestCase):

    def test_choice_page_links_to_both_signups(self):
        r = self.client.get(reverse("accounts:register"))
        self.assertContains(r, reverse("accounts:register_student"))
        self.assertContains(r, reverse("accounts:register_company"))

    def test_student_can_register(self):
        r = self.client.post(reverse("accounts:register_student"), signup_data())
        self.assertRedirects(r, reverse("accounts:login"))
        user = User.objects.get(username="2510052")
        self.assertEqual(user.role, "student")
        self.assertNotEqual(user.password, PASSWORD)   # stored hashed, not plain

    def test_student_needs_university_email(self):
        self.client.post(reverse("accounts:register_student"),
                         signup_data(email="sara@gmail.com"))
        self.assertFalse(User.objects.filter(username="20230001").exists())

    def test_role_cannot_be_forged(self):
        self.client.post(reverse("accounts:register_student"),
                         signup_data(role="coordinator"))
        self.assertEqual(User.objects.get(username="20230001").role, "student")

    def test_company_can_register(self):
        r = self.client.post(reverse("accounts:register_company"), signup_data(
            username="acme_hr", email="omar@acme.com", company_name="Acme Corp"))
        self.assertRedirects(r, reverse("accounts:login"))
        user = User.objects.get(username="acme_hr")
        self.assertEqual(user.role, "company_rep")
        self.assertEqual(user.company_name, "Acme Corp")

    def test_company_rejects_gmail_and_university_email(self):
        for email in ("omar@gmail.com", "omar@huniversity.edu"):
            self.client.post(reverse("accounts:register_company"), signup_data(
                username="acme_hr", email=email, company_name="Acme Corp"))
            self.assertFalse(User.objects.filter(username="acme_hr").exists())


class LoginTests(TestCase):

    def setUp(self):
        # runs before every test in this class
        User.objects.create_user("2510052", "sara@haigazian.edu.lb", PASSWORD)

    def test_valid_login_redirects_to_home(self):
        r = self.client.post(reverse("accounts:login"),
                             {"username": "2510052", "password": PASSWORD})
        self.assertRedirects(r, reverse("accounts:home"))

    def test_invalid_login_shows_message(self):
        r = self.client.post(reverse("accounts:login"),
                             {"username": "2510052", "password": "wrong"})
        self.assertContains(r, "Invalid credentials")

    def test_home_requires_login(self):
        r = self.client.get(reverse("accounts:home"))
        self.assertRedirects(
            r, f"{reverse('accounts:login')}?next={reverse('accounts:home')}")