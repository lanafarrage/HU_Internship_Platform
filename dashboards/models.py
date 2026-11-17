from django.conf import settings
from django.db import models


class Internship(models.Model):
    CATEGORY_CHOICES = [
        ("Software Engineering", "Software Engineering"),
        ("Data Science", "Data Science"),
        ("Cybersecurity", "Cybersecurity"),
        ("IT & Support", "IT & Support"),
    ]

    company = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="internship_listings",
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    required_skills = models.TextField(help_text="Comma-separated, e.g. Python, Django, SQL")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="Software Engineering")
    deadline = models.DateField()
    location = models.CharField(max_length=150)
    duration = models.CharField(max_length=80, blank=True)  # e.g. "3 months"
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title