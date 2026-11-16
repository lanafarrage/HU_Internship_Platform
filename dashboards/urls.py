from django.urls import path
from . import views

app_name = "dashboards"

urlpatterns = [
    path("student/", views.student_dashboard, name="student"),
    path("company/", views.company_dashboard, name="company"),
    path("coordinator/", views.coordinator_dashboard, name="coordinator"),
    path("supervisor/", views.supervisor_dashboard, name="supervisor"),
    path("internships/new/", views.internship_create, name="internship_create"),
    path("internships/<int:pk>/edit/", views.internship_edit, name="internship_edit"),
    path("internships/<int:pk>/close/", views.internship_close, name="internship_close"),
    path("internships/<int:pk>/delete/", views.internship_delete, name="internship_delete"),
]