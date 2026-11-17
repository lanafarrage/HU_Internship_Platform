from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.permissions import role_required
from dashboards.models import Internship
from profiles.models import Skill, StudentProfile, StudentSkill
from .forms import StudentProfileForm
from .models import InternshipApplication
from .recommender import parse_skills, profile_text, recommend


def get_student_profile(request):
    profile, _ = StudentProfile.objects.get_or_create(
        user=request.user,
        defaults={'full_name': request.user.get_full_name() or request.user.username},
    )
    return profile


@role_required("student")
def browse_internships(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    location_filter = request.GET.get('location', '')
    sort_by = request.GET.get('sort', 'date')

    listings = Internship.objects.filter(is_open=True).select_related('company')

    if query:
        listings = listings.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(required_skills__icontains=query)
        )
    if category and category != 'All':
        listings = listings.filter(category=category)
    if location_filter and location_filter != 'All':
        listings = listings.filter(location__icontains=location_filter)

    listings = listings.order_by('title') if sort_by == 'name' else listings.order_by('deadline')

    student = get_student_profile(request)
    applied_ids = set(
        InternshipApplication.objects.filter(student=student).values_list('listing_id', flat=True)
    )

    return render(request, 'internships/browse.html', {
        'listings': listings,
        'applied_ids': applied_ids,
        'query': query,
        'selected_category': category,
        'selected_location': location_filter,
        'sort_by': sort_by,
    })


@role_required("student")
def apply_internship(request, pk):
    listing = get_object_or_404(Internship, pk=pk, is_open=True)
    student = get_student_profile(request)

    if listing.deadline < timezone.localdate():
        messages.error(request, "The deadline for this internship has passed.")
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


@role_required("student")
def recommended_internships(request):
    student = get_student_profile(request)

    skills = [ss.skill.name for ss in student.student_skills.select_related('skill')]
    applied_ids = InternshipApplication.objects.filter(student=student).values_list('listing_id', flat=True)

    candidates = (
        Internship.objects.filter(is_open=True, deadline__gte=timezone.localdate())
        .exclude(id__in=applied_ids)
        .select_related('company')
    )
    results = recommend(skills, profile_text(student), candidates, limit=6)

    return render(request, 'internships/recommended.html', {
        'results': results,
        'has_skills': bool(skills),
    })


@role_required("student")
def my_applications(request):
    student = get_student_profile(request)
    applications = (
        InternshipApplication.objects.filter(student=student)
        .select_related('listing', 'listing__company')
        .order_by('-applied_at')
    )
    return render(request, 'internships/my_applications.html', {'applications': applications})


@role_required("student")
def student_profile(request):
    profile = get_student_profile(request)
    form = StudentProfileForm(instance=profile)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_profile':
            old_cv = profile.cv.name if profile.cv else None
            form = StudentProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
                if old_cv and old_cv != profile.cv.name:
                    profile.cv.storage.delete(old_cv)
                messages.success(request, "Profile saved.")
                return redirect('student_profile')

        elif action == 'add_skill':
            level = request.POST.get('level', '')
            if level not in ('beginner', 'intermediate', 'advanced'):
                level = ''
            names = parse_skills(request.POST.get('skill', ''))
            if not names:
                messages.error(request, "Type at least one skill.")
            for name in names:
                name = name[:80]
                skill = Skill.objects.filter(name__iexact=name).first() or Skill.objects.create(name=name)
                StudentSkill.objects.get_or_create(
                    profile=profile, skill=skill, defaults={'level': level}
                )
            if names:
                messages.success(request, "Skills updated.")
            return redirect('student_profile')

        elif action == 'remove_skill':
            skill_id = request.POST.get('skill_id', '')
            if skill_id.isdigit():
                StudentSkill.objects.filter(pk=skill_id, profile=profile).delete()
                messages.success(request, "Skill removed.")
            return redirect('student_profile')

    skills = profile.student_skills.select_related('skill').order_by('skill__name')
    return render(request, 'internships/profile.html', {
        'form': form,
        'profile': profile,
        'skills': skills,
    })