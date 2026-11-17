from django.contrib import admin
from .models import InternshipApplication


@admin.register(InternshipApplication)
class InternshipApplicationAdmin(admin.ModelAdmin):
    list_display = ("student", "listing", "status", "applied_at")
    list_filter = ("status",)