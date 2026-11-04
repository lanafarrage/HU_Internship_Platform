import os 
from rest_framework import serializers
from .models import Document

# SET THE FILE SIZE
Max_file_size = 10*1024*1024
Allowed_Extensions = {".pdf"}


class DocumentSerializer(serializers.ModelSerializer):
    class Meta :
        model = Document
        fields = [
            "id", "placement", "document_type", "file",
            "original_name", "uploaded_by", "uploaded_at",
        ]
        read_only_fields = ["uploaded_by", "uploaded_at", "original_name"]
    
    def validate_file(self, file):
        ext = os.path.splitext (file.name)[1].lower()
        if ext not in Allowed_Extensions:
            raise serializers.ValidationError("The file must be in the PDF format")
        
        if file.size > Max_file_size:
            raise serializers.ValidationError("The file size must be 10 MB or smaller")
        
        return file
    
    def validate_placement(self, placement):
        user = self.context["request"].user
        if placement.student != user:
            raise serializers.ValidationError("This is not your placements")
        
        return placement

