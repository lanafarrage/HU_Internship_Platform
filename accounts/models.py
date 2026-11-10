from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
ROLE_CHOICES = [
        ("student", "Student"),
        ("coordinator", "University Coordinator"),
        ("supervisor", "Faculty Supervisor"),
        ("company_rep", "Company Representative")
]
class User(AbstractUser):
    email = models.EmailField(unique=True) # one account per email
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student") 
    company_name = models.CharField(max_length=150, blank=True) #only used by company reps
 