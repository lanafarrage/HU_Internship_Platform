from types import SimpleNamespace
from django.test import SimpleTestCase
from .recommender import recommend


def fake(title, category, requirements, description=''):
    return SimpleNamespace(title=title, category=category,
                           requirements=requirements, description=description)


class RecommenderTests(SimpleTestCase):
    def setUp(self):
        self.web = fake('Django Backend Intern', 'Software Engineering', 'Python, Django, SQL')
        self.sec = fake('SOC Analyst Intern', 'Cybersecurity', 'Networking, Linux, SIEM')

    def test_best_match_ranks_first(self):
        results = recommend('Python Django SQL databases', [self.sec, self.web])
        self.assertEqual(results[0]['listing'], self.web)

    def test_matched_keywords_returned(self):
        results = recommend('Python Django', [self.web])
        self.assertIn('django', results[0]['matched'])

    def test_empty_profile_returns_nothing(self):
        self.assertEqual(recommend('', [self.web]), [])