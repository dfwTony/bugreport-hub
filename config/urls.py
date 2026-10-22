from django.contrib import admin
from django.urls import include, path

from tracker import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("register/", views.register, name="register"),
    path("", views.dashboard, name="dashboard"),
    path("reports/", views.report_list, name="report_list"),
    path("reports/new/", views.report_create, name="report_create"),
    path("reports/<int:pk>/", views.report_detail, name="report_detail"),
    path("notifications/", views.notifications, name="notifications"),
    path("summary/", views.summary, name="summary"),
]