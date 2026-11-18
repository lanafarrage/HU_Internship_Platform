import json
import logging

from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger(__name__)

MAX_ITEMS = 15      # keeps the AI's input small (the free tier has a token limit)
MAX_MATCHES = 5


# ---------------- Shared helpers ----------------

def _open_listings():
    """Same rule as the browse page: open and not past its deadline."""
    from dashboards.models import Internship
    return Internship.objects.filter(
        is_open=True, deadline__gte=timezone.localdate()
    ).select_related("company")


def _keyword_filter(queryset, keyword):
    keyword = str(keyword or "").strip()[:100]
    if keyword:
        queryset = queryset.filter(
            Q(title__icontains=keyword) | Q(description__icontains=keyword)
            | Q(required_skills__icontains=keyword) | Q(location__icontains=keyword)
            | Q(category__icontains=keyword)
        )
    return queryset


def _company_name(listing):
    return listing.company.company_name or listing.company.username


def _listing_info(listing):
    from internships.recommender import parse_skills
    return {
        "id": listing.pk,
        "title": listing.title,
        "company": _company_name(listing),
        "category": getattr(listing, "category", ""),
        "location": listing.location,
        "required_skills": parse_skills(listing.required_skills),
        "deadline": listing.deadline.isoformat(),
    }


def _student_profile(user):
    """The student's profile, or None. Read-only: never creates one."""
    from profiles.models import StudentProfile
    return StudentProfile.objects.filter(user=user).first()


def _student_skills(profile):
    return [ss.skill.name for ss in profile.student_skills.select_related("skill")]


# ---------------- Tools for everyone ----------------

def _account_info(user, args):
    data = {
        "username": user.username,
        "name": user.get_full_name(),
        "role": user.get_role_display(),
    }
    if user.role == "company_rep":
        data["company_name"] = user.company_name
    return data


# ---------------- Student / coordinator / supervisor ----------------

def _open_internships(user, args):
    queryset = _keyword_filter(_open_listings(), args.get("keyword")).order_by("deadline")
    total = queryset.count()
    items = []
    for listing in queryset[:MAX_ITEMS]:
        info = _listing_info(listing)
        info["summary"] = listing.description[:200]
        items.append(info)
    return {"total_open": total, "showing": len(items), "internships": items}


# ---------------- Student only ----------------

def _my_recommendations(user, args):
    from internships.models import InternshipApplication
    from internships.recommender import profile_text, recommend

    profile = _student_profile(user)
    if profile is None:
        return {"has_profile": False,
                "message": "This student has no profile yet. Tell them to open "
                           "'My profile' and add their skills."}

    skills = _student_skills(profile)
    if not skills:
        return {"has_profile": True, "has_skills": False,
                "message": "This student has not added any skills yet, so matches "
                           "can't be calculated. Tell them to add skills on 'My profile'."}

    applied = InternshipApplication.objects.filter(student=profile).values_list("listing_id", flat=True)
    candidates = _keyword_filter(_open_listings(), args.get("keyword")).exclude(id__in=applied)
    results = recommend(skills, profile_text(profile), candidates, limit=MAX_MATCHES)

    recommendations = []
    for r in results:
        info = _listing_info(r["listing"])
        info["match_score_percent"] = r["score"]
        info["skills_you_have"] = r["matched"]
        info["skills_you_are_missing"] = r["missing"]
        recommendations.append(info)

    result = {"has_skills": True, "your_skills": skills,
              "count": len(recommendations), "recommendations": recommendations}
    if not recommendations:
        result["message"] = "No open internship currently matches this student's skills."
    return result


def _my_applications(user, args):
    from internships.models import InternshipApplication

    profile = _student_profile(user)
    if profile is None:
        return {"count": 0, "applications": []}

    applications = (
        InternshipApplication.objects.filter(student=profile)
        .select_related("listing", "listing__company")
        .order_by("-applied_at")
    )
    items = [
        {
            "title": a.listing.title,
            "company": _company_name(a.listing),
            "status": a.status,
            "applied_on": a.applied_at.date().isoformat(),
        }
        for a in applications[:MAX_ITEMS]
    ]
    return {"count": applications.count(), "applications": items}


# ---------------- Company representative only ----------------

def _own_listings(user):
    """Only this company's listings, each with applicant counts."""
    from dashboards.models import Internship
    return Internship.objects.filter(company=user).annotate(
        applicant_total=Count("applications"),
        pending_total=Count("applications", filter=Q(applications__status="Pending")),
        accepted_total=Count("applications", filter=Q(applications__status="Accepted")),
        rejected_total=Count("applications", filter=Q(applications__status="Rejected")),
    ).order_by("-deadline")


def _listing_summary(listing):
    return {
        "id": listing.pk,
        "title": listing.title,
        "is_open": listing.is_open,
        "accepting_applications": listing.is_open and listing.deadline >= timezone.localdate(),
        "deadline": listing.deadline.isoformat(),
        "applicants": listing.applicant_total,
        "pending": listing.pending_total,
        "accepted": listing.accepted_total,
        "rejected": listing.rejected_total,
    }


def _top_applicants(listing):
    """Best-matching applicants for one listing, using the same skill matching as the recommender."""
    from internships.models import InternshipApplication
    from internships.recommender import parse_skills, skill_match

    required = parse_skills(listing.required_skills)
    rows = []
    applications = (
        InternshipApplication.objects.filter(listing=listing)
        .select_related("student")
        .prefetch_related("student__student_skills__skill")
    )
    for application in applications:
        skills = [ss.skill.name for ss in application.student.student_skills.all()]
        matched, _missing = skill_match(skills, required)
        score = round(100 * len(matched) / len(required)) if required else None
        rows.append({
            "name": application.student.full_name,
            "status": application.status,
            "match_score_percent": score,
            "skills_matched": matched,
        })
    rows.sort(key=lambda r: (r["match_score_percent"] is None, -(r["match_score_percent"] or 0)))
    return rows[:MAX_MATCHES]


def _list_my_internships(user, args):
    listings = _own_listings(user)
    return {"total": listings.count(),
            "internships": [_listing_summary(l) for l in listings[:MAX_ITEMS]]}


def _count_applicants(user, args):
    title = str(args.get("title", "")).strip()[:100]
    if not title:
        return {"error": "Ask which internship they mean (part of its title is enough)."}

    own = _own_listings(user)
    matches = list(own.filter(title__icontains=title)[:MAX_MATCHES])
    if not matches:
        return {"error": "None of this company's internships match that title.",
                "your_titles": [l.title for l in own[:MAX_ITEMS]]}

    result = {"matches": [_listing_summary(l) for l in matches]}
    if len(matches) == 1:
        result["top_applicants"] = _top_applicants(matches[0])
    else:
        result["note"] = "Several internships match. Report each one, or ask which is meant."
    return result


# ---------------- Registry ----------------
# roles=None means every role may use the tool; otherwise list the allowed roles.

TOOLS = {
    "get_my_account_info": {
        "roles": None,
        "description": "Get the logged-in user's own name, role and company name.",
        "parameters": {"type": "object", "properties": {}},
        "func": _account_info,
    },
    "list_open_internships": {
        "roles": ["student", "coordinator", "supervisor"],
        "description": (
            "List the internships that are currently open for applications. "
            "Optionally filter by a keyword matching title, skills, location, category or "
            "description. Always use this when asked what internships are available."
        ),
        "parameters": {
            "type": "object",
            "properties": {"keyword": {
                "type": "string",
                "description": "Optional word to filter by, e.g. 'front end' or 'Python'."}},
        },
        "func": _open_internships,
    },
    "get_my_recommendations": {
        "roles": ["student"],
        "description": (
            "Get the best-matching open internships for the logged-in student, ranked by how "
            "many required skills they have. Use for 'what is best for me', 'what should I "
            "apply to' or 'which internships match my skills'. Optional keyword narrows the "
            "search, e.g. 'front end'."
        ),
        "parameters": {
            "type": "object",
            "properties": {"keyword": {
                "type": "string", "description": "Optional topic to narrow the matches."}},
        },
        "func": _my_recommendations,
    },
    "get_my_applications": {
        "roles": ["student"],
        "description": (
            "List the logged-in student's own applications with their status "
            "(Pending, Accepted or Rejected). Use for 'did I apply to...' or "
            "'what is the status of my applications'."
        ),
        "parameters": {"type": "object", "properties": {}},
        "func": _my_applications,
    },
    "list_my_internships": {
        "roles": ["company_rep"],
        "description": (
            "List the internships posted by the logged-in company, with whether each is open "
            "and how many applicants it has."
        ),
        "parameters": {"type": "object", "properties": {}},
        "func": _list_my_internships,
    },
    "count_applicants": {
        "roles": ["company_rep"],
        "description": (
            "Count the applicants (and their statuses) for the company's own internship, found "
            "by part of its title. For a single match it also lists the best-matching "
            "applicants. Use for 'how many applied to our front end internship'."
        ),
        "parameters": {
            "type": "object",
            "properties": {"title": {
                "type": "string", "description": "Part of the internship title."}},
            "required": ["title"],
        },
        "func": _count_applicants,
    },
}


def _allowed(tool, role):
    return tool["roles"] is None or role in tool["roles"]


def tools_for_role(role):
    """The tool descriptions sent to the AI. Only tools this role may use."""
    return [
        {"type": "function",
         "function": {"name": name, "description": t["description"],
                      "parameters": t["parameters"]}}
        for name, t in TOOLS.items() if _allowed(t, role)
    ]


def run_tool(name, raw_arguments, user):
    """Run a tool the AI asked for and return the result as a JSON string.
    Never raises: problems are reported back to the AI as an error message."""
    tool = TOOLS.get(name)
    if tool is None or not _allowed(tool, user.role):
        return json.dumps({"error": "This tool is not available."})
    try:
        args = json.loads(raw_arguments or "{}")
        if not isinstance(args, dict):
            raise ValueError
    except ValueError:
        return json.dumps({"error": "Invalid tool arguments."})
    try:
        return json.dumps(tool["func"](user, args), default=str)
    except Exception:
        logger.exception("Tool %s failed", name)
        return json.dumps({"error": "The tool failed."})