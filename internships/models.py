from django.db import models


class InternshipApplication(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    listing = models.ForeignKey('dashboards.Internship', on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey('profiles.StudentProfile', on_delete=models.CASCADE)
    cover_letter = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.listing.title}"