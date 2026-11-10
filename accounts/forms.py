from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User

    
class StudentRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")
        labels = {"username": "Univeristy ID"}
    
    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        domain = settings.UNIVERSITY_EMAIL_DOMAIN
        if not email.endswith
            raise forms.ValidationError(f"Please use your university email address (@{domain}).")
        return email

class CompanyRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "company_name")
        labels = {"email": "Work email"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["company_name"].required = True   # model allows blank, form doesn't

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        domain = email.split("@")[-1]
        if domain == settings.UNIVERSITY_EMAIL_DOMAIN:
            raise forms.ValidationError("University emails must register as students.")
        if domain in ("gmail.com", "yahoo.com", "hotmail.com", "outlook.com"):
            raise forms.ValidationError("Please use your company email address.")
        return email

class LoginForm(AuthenticationForm):
    username = forms.CharField(label="University ID / Username")
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Invalid credentials. Please check your ID/username and password.",
    }