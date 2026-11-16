from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


from accounts.permissions import role_required

from .forms import InternshipForm
from .models import Internship


@role_required("student")
def student_dashboard(request):
    return render(request, "dashboards/student.html")


@role_required("company_rep")
def company_dashboard(request):
    internships = Internship.objects.filter(company=request.user)
    return render(request, "dashboards/company-view.html", {
        "internships": internships,
        "open_count": internships.filter(is_open=True).count(),
        "closed_count": internships.filter(is_open=False).count(),
    })


@role_required("company_rep")
def internship_create(request):
    form = InternshipForm(request.POST or None)
    if form.is_valid():
        internship = form.save(commit=False)
        internship.company = request.user  # set by the server
        internship.save()
        messages.success(request, "Listing created.")
        return redirect("dashboards:company")
    return render(request, "dashboards/internship_form.html",
                  {"form": form, "page_title": "Create internship listing"})


@role_required("company_rep")
def internship_edit(request, pk):
    internship = get_object_or_404(Internship, pk=pk, company=request.user)
    form = InternshipForm(request.POST or None, instance=internship)
    if form.is_valid():
        form.save()
        messages.success(request, "Listing updated.")
        return redirect("dashboards:company")
    return render(request, "dashboards/internship_form.html",
                  {"form": form, "page_title": "Edit internship listing"})


@role_required("company_rep")
@require_POST
def internship_close(request, pk):
    internship = get_object_or_404(Internship, pk=pk, company=request.user)
    internship.is_open = False
    internship.save()
    messages.success(request, "Listing closed.")
    return redirect("dashboards:company")


@role_required("company_rep")
def internship_delete(request, pk):
    internship = get_object_or_404(Internship, pk=pk, company=request.user)
    if request.method == "POST":
        internship.delete()
        messages.success(request, "Listing deleted.")
        return redirect("dashboards:company")
    return render(request, "dashboards/internship_confirm_delete.html",
                  {"internship": internship})


@role_required("coordinator")
def coordinator_dashboard(request):
    return render(request, "dashboards/coordinator.html")


@role_required("supervisor")
def supervisor_dashboard(request):
    return render(request, "dashboards/supervisor.html")

@login_required
def home_view(request):
    target = ROLE_HOME.get(request.user.role)
    if target:
        return redirect(target)
    messages.error(request, "Invalid role. Please contact support.")
    return redirect("accounts:login")