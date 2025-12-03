from django.urls import path

from . import views

urlpatterns = [
    path("", views.gb_index, name="gb-index"),
    path("teachers", views.teacher_list, name="teacher-list"),
    path("course", views.course_list, name="course-list"),
    # path("grade-entry", views.grade_entry, name="grade-entry"),
    path("grade-entry", views.GradeEntryForm.as_view(), name="grade-entry"),
    path("attendance", views.attendance, name="student-attendance")
    ]