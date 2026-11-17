from django.db import models
from django.conf import settings


class Internship(models.Model):
    company = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="internship_listings",
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    required_skills = models.TextField()
    deadline = models.DateField()
    location = models.CharField(max_length=150)
    is_open = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    duration = models.CharField(max_length=80, blank=True)  # e.g. "3 months"