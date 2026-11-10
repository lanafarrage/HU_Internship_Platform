from django.contrib import admin
from .models import InternshipListing, InternshipApplication

admin.site.register(InternshipListing)
admin.site.register(InternshipApplication)