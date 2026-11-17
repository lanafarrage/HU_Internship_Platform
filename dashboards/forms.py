from django import forms

from .models import Internship


class InternshipForm(forms.ModelForm):
    class Meta:
        model = Internship
        fields = (
            "title",
            "category",
            "description",
            "required_skills",
            "deadline",
            "location",
            "duration",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "required_skills": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Comma-separated, e.g. Python, Django, SQL"}
            ),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }