import os
from rest_framework import serializers
from .models import StudentProfile, Skill, StudentSkill

MAX_CV_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_CV_EXTENSIONS = {".pdf", ".docx"}


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ["id", "name"]


class StudentSkillSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.name", read_only=True)

    class Meta:
        model = StudentSkill
        fields = ["id", "skill", "skill_name", "level"]


class StudentProfileSerializer(serializers.ModelSerializer):
    student_skills = StudentSkillSerializer(many=True, read_only=True)

    class Meta:
        model = StudentProfile
        exclude = ["user"]
        read_only_fields = ["updated_at"]

    def validate_cv(self, file):
        if file is None:
            return file
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALLOWED_CV_EXTENSIONS:
            raise serializers.ValidationError("CV must be a PDF or DOCX file.")
        if file.size > MAX_CV_SIZE:
            raise serializers.ValidationError("CV must be 5 MB or smaller.")
        return file

    def update(self, instance, validated_data):
        old_name = instance.cv.name if instance.cv else None
        instance = super().update(instance, validated_data)
        new_name = instance.cv.name if instance.cv else None
        # delete the old file from disk once a new one has replaced it
        if "cv" in validated_data and old_name and old_name != new_name:
            instance.cv.storage.delete(old_name)
        return instance
