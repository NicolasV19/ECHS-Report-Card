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