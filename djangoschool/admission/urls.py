# -*- coding: utf-8 -*-

from django.urls import path

from . import views

urlpatterns = [
    path("", views.AdmissionView.as_view(), name="adm-index")
    ]