from django.db import models
from django.conf import settings

# Create your models here.

class StudentProfile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
    )
    full_name = models.CharField(max_length = 100)
    about_me = models.TextField(blank=True)
    experience = models.TextField(blank=True)
    education = models.TextField(blank=True)
    #skills = models.TextField(blank=True)

    certification = models.ImageField(
        upload_to="certification",
        blank=True,
        null=True,
    )
    cv = models.FileField(
        upload_to="student_cvs/",
        blank=True,
        null=True
    )

    #Personal Details
    Gender_Choice = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]
    gender = models.CharField(
        max_length= 20,
        choices= Gender_Choice,
        blank=True,
    )

    DOB = models.DateField(
        null=True,
        blank=True,
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True
    )
    LANGUAGE_CHOICES = [
        ("english", "English"),
        ("french", "French"),
        ("arabic", "Arabic"),
        ("other", "Other"),
    ]

    language = models.CharField(
        max_length=20,
        choices=LANGUAGE_CHOICES,
        blank=True
    )
    nationality = models.CharField(
        max_length=100,
        blank=True
    )
    # Social links
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name


class Skill(models.Model):
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name


class StudentSkill(models.Model):
    profile = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name="student_skills"
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.CharField(max_length=20, blank=True)  # beginner / intermediate / advanced

    class Meta:
        unique_together = ("profile", "skill")

    def __str__(self):
        return f"{self.profile.full_name} - {self.skill.name}"