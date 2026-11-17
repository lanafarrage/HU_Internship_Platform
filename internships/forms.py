from django import forms
from profiles.models import StudentProfile

MAX_CV_BYTES = 5 * 1024 * 1024
ALLOWED_CV_EXTENSIONS = ('.pdf', '.docx')


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ('full_name', 'about_me', 'experience', 'education', 'cv')
        widgets = {
            'about_me': forms.Textarea(attrs={'rows': 4}),
            'experience': forms.Textarea(attrs={'rows': 4}),
            'education': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {'cv': 'Accepted: PDF or DOCX, up to 5 MB.'}

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if cv and hasattr(cv, 'content_type'):
            if not cv.name.lower().endswith(ALLOWED_CV_EXTENSIONS):
                raise forms.ValidationError('CV must be a PDF or DOCX file.')
            if cv.size > MAX_CV_BYTES:
                raise forms.ValidationError('CV must be 5 MB or smaller.')
        return cv