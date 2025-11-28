from django.shortcuts import render
from django.http import HttpResponse
from gradebook.forms import GradeEntryForm
from gradebook.models import GradeEntry, AcademicYear
from gradebook.signals import *
from django.shortcuts import redirect

# Create your views here.
def gb_index(request):
    return render(request, "partials/gradebook/index.html")

def teacher_list(request):
    return HttpResponse("pass")

def course_list(request):
    return HttpResponse("pass")

def grade_entry(request):
    # entry = GradeEntry.objects.get(pk=id)
    # form = GradeEntryForm(instance=entry)
    form = GradeEntryForm()
    if request.method =='POST':
        form = GradeEntryForm(request.POST)
        if form.is_valid():
            new_grade_entry.send(sender=form)

    context = {'form': form}
    return render(request, "partials/gradebook/entry.html", context)

    
    # context = {'form': form }
    # return render(request, "partials/gradebook/entry.html", context)

def get_period(request):
    pass