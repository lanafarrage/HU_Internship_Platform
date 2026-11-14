from django.urls import path
from . import views

app_name = "dashboards"

urlpatterns = [
    path("student/", views.student_dashboard, name="student"),
    path("company/", views.company_dashboard, name="company"),
    path("coordinator/", views.coordinator_dashboard, name="coordinator"),
    path("supervisor/", views.supervisor_dashboard, name="supervisor"),
]