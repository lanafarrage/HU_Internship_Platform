from django.shortcuts import render
from accounts.permissions import role_required


@role_required("student")
def student_dashboard(request):
    return render(request, "dashboards/student.html")


@role_required("company_rep")
def company_dashboard(request):
    return render(request, "dashboards/company-view.html")


@role_required("coordinator")
def coordinator_dashboard(request):
    return render(request, "dashboards/coordinator.html")


@role_required("supervisor")
def supervisor_dashboard(request):
    return render(request, "dashboards/supervisor.html")