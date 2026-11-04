from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Placement, Document

admin.site.register(Placement)
admin.site.register(Document)