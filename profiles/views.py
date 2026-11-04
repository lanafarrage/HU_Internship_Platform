from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import Skill, StudentProfile, StudentSkill
from .serializers import SkillSerializer, StudentProfileSerializer, StudentSkillSerializer


def get_profile(user):
    profile, _ = StudentProfile.objects.get_or_create(
        user=user, defaults={"full_name": user.username}
    )
    return profile


class ProfileMeView(RetrieveUpdateAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self):
        return get_profile(self.request.user)


class SkillListView(ListAPIView):
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Skill.objects.order_by("name")
        search = self.request.query_params.get("search")
        return qs.filter(name__icontains=search) if search else qs


class MySkillViewSet(ModelViewSet):
    serializer_class = StudentSkillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # only the logged-in student's own skills
        return StudentSkill.objects.filter(
            profile__user=self.request.user
        ).select_related("skill")

    def _check_duplicate(self, profile, skill, exclude_id=None):
        qs = StudentSkill.objects.filter(profile=profile, skill=skill)
        if exclude_id:
            qs = qs.exclude(pk=exclude_id)
        if qs.exists():
            raise ValidationError("You already have this skill.")

    def perform_create(self, serializer):
        profile = get_profile(self.request.user)
        self._check_duplicate(profile, serializer.validated_data["skill"])
        serializer.save(profile=profile)

    def perform_update(self, serializer):
        skill = serializer.validated_data.get("skill")
        if skill:
            self._check_duplicate(serializer.instance.profile, skill, serializer.instance.pk)
        serializer.save()
