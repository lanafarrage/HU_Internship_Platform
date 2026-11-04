from django.shortcuts import render

from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated

from .models import Document
from .serializers import DocumentSerializer

# Create your views here.

def is_review(user):
    return user.is_staff

class DocumentListCreateView(ListCreateAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser , FormParser]
    def get_queryset(self):
        qs = Document.objects.select_related("placement")
        if is_review(self.request.user):
            return qs
        return qs.filter(placement__student=self.request.user)

    def perform_create(self, serializer):
        f = serializer.validated_data["file"]
        serializer.save(uploaded_by=self.request.user, original_name=f.name)

def get_queryset(self):
    qs = Document.objects.select_related("placement")

    if is_review(self.request.user):
        return qs
    return qs.filter(placement_student =  self.request.user)

def perform_create(self, serializer):
    
    fun = serializer.validated_data["file"]
    serializer.save(uploaded_by=self.request.user, original_name=fun.name)

class DocumentDetailView(RetrieveAPIView):
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs= Document.objects.select_related("placement")
        if is_review(self.request.user):
            return qs
        return qs.filter(placement__student=self.request.user)