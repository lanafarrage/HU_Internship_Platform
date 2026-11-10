from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from .forms import StudentReisterForm, CompanyRegisterForm

def register_choice_view(request):
    error = None
    if request.method == "POST":
        choice = request.POST.get("account_type")
        if choice == "student"
            return redirect("accounts:register_student")
        if choice == "company":
            return redirect("accounts:register_company")
        error = "Please select an account type to continue."
    return render(request, "accounts/role.html", {"error": error})

def register_student_view(request):
    form = StudentRegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.role = "student"
        user.save()
        messages.success(request, "Account created! You can now log in.")
        return redirect("accounts:login")
    return render(request, "accounts/signup.html",
    {"form": form, "is_company": False})

def register_company_view(request):
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
    user = request.user
    if user.role == "student":
        return render(request, "accounts/student_home.html")
    elif user.role == "coordinator":
        return render(request, "accounts/coordinator_home.html")
    elif user.role == "supervisor":
        return render(request, "accounts/supervisor_home.html")
    elif user.role == "company_rep":
        return render(request, "accounts/company_home.html")
    else:
        messages.error(request, "Invalid role. Please contact support.")
        return redirect("accounts:login")


