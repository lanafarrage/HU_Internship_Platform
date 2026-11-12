from django.urls import path
from . import views

urlpatterns = [
    path('browse/', views.browse_internships, name='browse_internships'),
    path('apply/<int:pk>/', views.apply_internship, name='apply_internship'),
    path('recommended/', views.recommended_internships, name='recommended_internships'),
]