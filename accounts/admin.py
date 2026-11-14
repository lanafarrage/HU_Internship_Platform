from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Role", {"fields": ("role", "company_name")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Role", {"fields": ("email", "role", "company_name")}),)
    list_display = ("username", "email", "role", "company_name", "is_active")
    list_filter = ("role", "is_active")