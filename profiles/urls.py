from django.urls import path
from .views import ProfileMeView

urlpatterns = [
    path("profile/me/", ProfileMeView.as_view(), name="profile-me"),
]