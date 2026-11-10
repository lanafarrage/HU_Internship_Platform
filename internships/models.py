from django.db import models


class InternshipListing(models.Model):
    CATEGORY_CHOICES = [
        ('Software Engineering', 'Software Engineering'),
        ('Data Science', 'Data Science'),
        ('Cybersecurity', 'Cybersecurity'),
        ('IT & Support', 'IT & Support'),
    ]
    
    LOCATION_CHOICES = [
        ('Beirut', 'Beirut'),
        ('Tripoli', 'Tripoli'),
        ('Byblos', 'Byblos'),
        ('Sidon', 'Sidon'),
        ('Remote', 'Remote'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField(help_text="Comma-separated skills like Python, Django, SQL")
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES, default='Beirut')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Software Engineering')
    duration = models.CharField(max_length=50)
    deadline = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return self.title


# THIS MUST BE UNINDENTED (At the root level, outside InternshipListing)
class InternshipApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]
    
    listing = models.ForeignKey(InternshipListing, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey('profiles.StudentProfile', on_delete=models.CASCADE)
    cover_letter = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.listing.title}"