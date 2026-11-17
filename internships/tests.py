from datetime import timedelta
from types import SimpleNamespace

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from dashboards.models import Internship
from profiles.models import Skill, StudentProfile, StudentSkill
from .models import InternshipApplication
from .recommender import parse_skills, recommend


class RecommenderTests(SimpleTestCase):
    def fake(self, title, skills):
        return SimpleNamespace(title=title, category='', required_skills=skills, description='')

    def test_parse_skills(self):
        self.assertEqual(parse_skills('Python, SQL;\nDocker'), ['Python', 'SQL', 'Docker'])

    def test_full_match_ranks_first(self):
        a = self.fake('Backend', 'Python, Django, SQL')
        b = self.fake('Security', 'Linux, Networking')
        results = recommend(['Python', 'Django', 'SQL'], '', [b, a])
        self.assertEqual(results[0]['listing'], a)
        self.assertEqual(results[0]['score'], 100)

    def test_missing_skills_reported(self):
        r = recommend(['Python'], '', [self.fake('Backend', 'Python, Docker')])[0]
        self.assertEqual(r['score'], 50)
        self.assertEqual(r['missing'], ['Docker'])

    def test_java_does_not_match_javascript(self):
        self.assertEqual(recommend(['Java'], '', [self.fake('Web', 'JavaScript')]), [])


class StudentFlowTests(TestCase):
    def setUp(self):
        self.company = User.objects.create_user(
            'acme', 'hr@acme.com', 'pass12345', role='company_rep', company_name='Acme')
        student = User.objects.create_user(
            'sara', 'sara@students.haigazian.edu.lb', 'pass12345', role='student')
        self.profile = StudentProfile.objects.create(user=student, full_name='Sara Test')
        StudentSkill.objects.create(profile=self.profile, skill=Skill.objects.create(name='Python'))

        soon = timezone.localdate() + timedelta(days=30)
        common = dict(company=self.company, description='d', deadline=soon,
                      location='Beirut', category='Software Engineering')
        self.open = Internship.objects.create(title='Open Role', required_skills='Python, SQL', **common)
        Internship.objects.create(title='Closed Role', required_skills='Python', is_open=False, **common)
        self.client.login(username='sara', password='pass12345')

    def test_browse_shows_only_open(self):
        resp = self.client.get(reverse('browse_internships'))
        self.assertContains(resp, 'Open Role')
        self.assertNotContains(resp, 'Closed Role')

    def test_apply_once(self):
        url = reverse('apply_internship', args=[self.open.pk])
        self.client.post(url, {'cover_letter': 'hi'})
        self.client.post(url, {'cover_letter': 'again'})
        self.assertEqual(InternshipApplication.objects.count(), 1)

    def test_recommended_shows_score(self):
        resp = self.client.get(reverse('recommended_internships'))
        self.assertContains(resp, '50% match')

    def test_my_applications_lists_applied(self):
        InternshipApplication.objects.create(listing=self.open, student=self.profile, cover_letter='x')
        resp = self.client.get(reverse('my_applications'))
        self.assertContains(resp, 'Open Role')

    def test_company_cannot_browse(self):
        self.client.login(username='acme', password='pass12345')
        self.assertEqual(self.client.get(reverse('browse_internships')).status_code, 403)

    def test_profile_created_on_first_visit(self):
        u = User.objects.create_user('newbie', 'n@students.haigazian.edu.lb', 'pass12345', role='student')
        self.client.login(username='newbie', password='pass12345')
        self.assertEqual(self.client.get(reverse('recommended_internships')).status_code, 200)
        self.assertTrue(StudentProfile.objects.filter(user=u).exists())

    def test_profile_page_loads(self):
        self.assertEqual(self.client.get(reverse('student_profile')).status_code, 200)

    def test_add_and_remove_skill(self):
        url = reverse('student_profile')
        self.client.post(url, {'action': 'add_skill', 'skill': 'Docker, linux', 'level': 'beginner'})
        names = set(self.profile.student_skills.values_list('skill__name', flat=True))
        self.assertEqual(names, {'Python', 'Docker', 'linux'})
        ss = self.profile.student_skills.get(skill__name='Docker')
        self.client.post(url, {'action': 'remove_skill', 'skill_id': ss.pk})
        self.assertFalse(self.profile.student_skills.filter(skill__name='Docker').exists())

    def test_save_profile_text(self):
        self.client.post(reverse('student_profile'), {
            'action': 'save_profile', 'full_name': 'Sara T',
            'about_me': 'Backend dev', 'experience': '', 'education': 'CS',
        })
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.about_me, 'Backend dev')

    def test_rejects_bad_cv(self):
        bad = SimpleUploadedFile('cv.exe', b'x', content_type='application/octet-stream')
        resp = self.client.post(reverse('student_profile'), {
            'action': 'save_profile', 'full_name': 'Sara', 'cv': bad,
        })
        self.assertContains(resp, 'CV must be a PDF or DOCX file.')