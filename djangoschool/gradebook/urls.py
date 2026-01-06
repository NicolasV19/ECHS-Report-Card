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
    path("report-card", views.ReportCardForm.as_view(), name="report-card"),
    path('get-teachers-ge/',views.get_teachers, name='get_teachers-ge'),
    path('get-courses/', views.get_courses, name='get_courses'),
    path('get-period-ge/', views.get_period_ge, name='get_period_ge'),
    path('get-courses-ge/', views.get_courses, name='get_courses_ge'),
    path('get-subjects-ge/', views.get_subjects_ge, name='get_subjects_ge'),
    path('reportcard-summary/', views.ReportCardGradeSummary.as_view(), name='reportcard-summary'),
    path('reportcard-summary-pdf-rplab/', views.report_card_summary_pdf_rplab, name='reportcard-summary-pdf-rplab'),
    path('reportcard-nonslick/', views.report_card_nonslick, name='reportcard-nonslick'),
    # path('reportcard_summary/', views.report_card_summary, name='reportcard_summary'),
    # path("finished-screen", views.finished, name="finished-screen")
    ]