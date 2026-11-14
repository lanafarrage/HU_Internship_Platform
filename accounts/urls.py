from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from . import views
from .forms import LoginForm

app_name = "accounts"

urlpatterns = [
    path("register/", views.register_choice_view, name="register"),
    path("register/student/", views.register_student_view, name="register_student"),
    path("register/company/", views.register_company_view, name="register_company"),
    path("login/", LoginView.as_view(
        template_name="accounts/login.html",
        authentication_form=LoginForm,
        redirect_authenticated_user=True,
    ), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("home/", views.home_view, name="home"),
]