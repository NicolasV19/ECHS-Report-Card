"""
URL configuration for django_sis project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from . import views
from debug_toolbar.toolbar import debug_toolbar_urls
from .admin import admin_statistics_view
# postgres stuff
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path(   # new
        "admin/statistics/",
        admin.site.admin_view(admin_statistics_view),
        name="admin-statistics"
    ),
    path("accounts/", include("account.urls")),
    path("admission/", include("admission.urls")),
    path("gradebook/", include("gradebook.urls")),
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
] + debug_toolbar_urls()

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

