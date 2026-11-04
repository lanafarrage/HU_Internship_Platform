from django.db import models
from django.conf import settings
# Create your models here.

class Placement(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name= "placements",
    )
    company_name = models.CharField(max_length=150)
    title = models.CharField(max_length=150)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.student} - {self.title} at {self.company_name}"
    
def document_upload_path(instance, filename):
    return f"documents/placement_{instance.placement_id}/{filename}"

class Document(models.Model):
    DOCUMENT_TYPES = [
        ("offer_letter", "Offer letter"),
        ("agreement", "Internship Agreement"),
        ("progress report","Progress Report"),
        ("final_report","Final Report"),
        ("other","Other"),
    ]

    placment = models.ForeignKey(
        Placement,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    upload_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete = models.CASCADE,
        related_name="aploaded_documents",
    )

    document_type = models.CharField(max_length=30 , choices=DOCUMENT_TYPES )
    file = models.FileField (upload_to=document_upload_path)
    original_name = models.CharField(max_length= 255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.placement}"