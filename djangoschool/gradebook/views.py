from django.shortcuts import render
from django.http import HttpResponse
from gradebook.forms import GradeEntryForm
from gradebook.models import GradeEntry, AcademicYear

# Create your views here.
def gb_index(request):
    return render(request, "partials/gradebook/index.html")

def teacher_list(request):
    return HttpResponse("pass")

def course_list(request):
    return HttpResponse("pass")

def grade_entry(request):
    entry = GradeEntry.objects.get(pk=3)
    form = GradeEntryForm(instance=entry)
    context = {'form': form }
    return render(request, "partials/gradebook/entry.html", context)

def get_period(request):
    pass