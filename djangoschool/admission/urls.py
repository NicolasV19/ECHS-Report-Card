# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path("", views.AdmissionView.as_view(), name="adm-index"),
    path("get-filter-options/", views.get_filter_options, name="get-filter-options"),
    path("get_student_counts/", views.get_student_counts, name="get_student_counts"),
    ]