from django import forms

from .models import Internship


class InternshipForm(forms.ModelForm):
    class Meta:
        model = Internship
        fields = (
            "title",
            "description",
            "required_skills",
            "deadline",
            "location",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "required_skills": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "List the skills required for this internship",
                }
            ),
            "deadline": forms.DateInput(attrs={"type": "date"}),
        }
