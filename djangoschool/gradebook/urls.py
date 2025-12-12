from django.urls import path

from . import views

urlpatterns = [
    path("", views.gb_index, name="gb-index"),
    path("teachers", views.teacher_list, name="teacher-list"),
    path("course", views.course_list, name="course-list"),
    # path("grade-entry", views.grade_entry, name="grade-entry"),
    path("grade-entry", views.GradeEntryForm.as_view(), name="grade-entry"),
    path("attendance", views.attendance, name="student-attendance"),
    path("midterm_pdf", views.midterm_report, name="midterm_report"),
    path("midterm_pdf_real/<int:student_id>/", views.midterm_report_pdf, name="midterm_report_pdf"),
    path("report-card", views.ReportCardForm.as_view(), name="report-card")
    # path("finished-screen", views.finished, name="finished-screen")
    ]