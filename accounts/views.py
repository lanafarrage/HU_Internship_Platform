from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import StudentRegisterForm, CompanyRegisterForm, LoginForm

# Where each role lands after login
ROLE_HOME = {
    "student": "dashboards:student",
    "company_rep": "dashboards:company",
    "coordinator": "dashboards:coordinator",
    "supervisor": "dashboards:supervisor",
}


class CustomLoginView(SuccessMessageMixin, LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True
    success_message = "Successfully logged in!"

    def get_success_url(self):
        # go back to the page they wanted, otherwise to their role's dashboard
        return self.get_redirect_url() or reverse(
            ROLE_HOME.get(self.request.user.role, "accounts:home"))


def register_choice_view(request):
    if request.user.is_authenticated:
        return redirect(ROLE_HOME.get(request.user.role, "accounts:home"))
    return render(request, "accounts/role.html")


def register_student_view(request):
    if request.user.is_authenticated:
        return redirect(ROLE_HOME.get(request.user.role, "accounts:home"))

    form = StudentRegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)   # password is already hashed here
        user.role = "student"            # set by the server, not the browser
        user.save()
        messages.success(request, "Account created! You can now log in.")
        return redirect("accounts:login")
    return render(request, "accounts/signup.html",
                  {"form": form, "is_company": False})


def register_company_view(request):
    if request.user.is_authenticated:
        return redirect(ROLE_HOME.get(request.user.role, "accounts:home"))

    form = CompanyRegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.role = "company_rep"
        user.save()
        messages.success(request, "Account created! You can now log in.")
        return redirect("accounts:login")
    return render(request, "accounts/signup.html",
                  {"form": form, "is_company": True})


@login_required
def home_view(request):
    target = ROLE_HOME.get(request.user.role)
    if target:
        return redirect(target)
    messages.error(request, "Invalid role. Please contact support.")
    return redirect("accounts:login")

def site_home(request):
    """The HUIntern logo link: dashboard if logged in, welcome page if not."""
    if request.user.is_authenticated:
        target = ROLE_HOME.get(request.user.role)
        if target:
            return redirect(target)
    return redirect("welcome")