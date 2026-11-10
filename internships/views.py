from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from profiles.models import StudentProfile
from .models import InternshipApplication, InternshipListing
from .recommender import profile_text, recommend


def get_current_student(request):
    # TODO: once login is integrated, return the logged-in user's profile here,
    # e.g. StudentProfile.objects.filter(user=request.user).first()
    return StudentProfile.objects.first()


def browse_internships(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    location_filter = request.GET.get('location', '')
    sort_by = request.GET.get('sort', 'date')

    listings = InternshipListing.objects.filter(is_archived=False)

    if query:
        listings = listings.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(requirements__icontains=query)
        )
    if category and category != 'All':
        listings = listings.filter(category__iexact=category)
    if location_filter and location_filter != 'All':
        listings = listings.filter(location__iexact=location_filter)

    listings = listings.order_by('title') if sort_by == 'name' else listings.order_by('deadline')

    return render(request, 'internships/browse.html', {
        'listings': listings,
        'query': query,
        'selected_category': category,
        'selected_location': location_filter,
        'sort_by': sort_by,
    })


def apply_internship(request, pk):
    listing = get_object_or_404(InternshipListing, pk=pk)
    student = get_current_student(request)

    if not student:
        messages.error(request, "Please create a student profile first.")
        return redirect('browse_internships')

    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '').strip()

        if InternshipApplication.objects.filter(listing=listing, student=student).exists():
            messages.warning(request, "You have already applied for this internship.")
        else:
            InternshipApplication.objects.create(
                listing=listing, student=student, cover_letter=cover_letter
            )
            messages.success(request, "Application submitted successfully!")
        return redirect('browse_internships')

    return render(request, 'internships/apply.html', {'listing': listing})


def recommended_internships(request):
    student = get_current_student(request)
    if not student:
        messages.error(request, "Please create a student profile first.")
        return redirect('browse_internships')

    applied_ids = InternshipApplication.objects.filter(
        student=student
    ).values_list('listing_id', flat=True)

    candidates = InternshipListing.objects.filter(
        is_archived=False, deadline__gte=timezone.localdate()
    ).exclude(id__in=applied_ids)

    text = profile_text(student)
    results = recommend(text, candidates, limit=6)

    return render(request, 'internships/recommended.html', {
        'results': results,
        'has_profile_text': bool(text.strip()),
    })