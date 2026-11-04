from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MySkillViewSet, ProfileMeView, SkillListView

router = DefaultRouter()
router.register("profile/me/skills", MySkillViewSet, basename="my-skills")

urlpatterns = [
    path("profile/me/", ProfileMeView.as_view(), name="profile-me"),
    path("skills/", SkillListView.as_view(), name="skill-list"),
    path("", include(router.urls)),
]
