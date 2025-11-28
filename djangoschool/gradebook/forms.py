from django import forms
from django.forms.models import ModelForm
from .models import GradeEntry


class GradeEntryForm(ModelForm):

    class Meta:
        model = GradeEntry
        fields = ["academic_year",
                  "period",
                  "teacher",
                  "subject",
                  "course"]
        widgets = {
                'academic_year': forms.Select(attrs={
                'class': 'form-select'
            }),
                'period': forms.Select(attrs={
                'class': 'form-select'
            }),
                'teacher': forms.Select(attrs={
                'class': 'form-select'
            }),
                'subject': forms.Select(attrs={
                'class': 'form-select'
            }),
                'course': forms.Select(attrs={
                'class': 'form-select'
            }),
        }