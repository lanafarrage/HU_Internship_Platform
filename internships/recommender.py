import math
import re
from collections import Counter

STOPWORDS = {
    'the', 'and', 'for', 'with', 'you', 'your', 'are', 'will', 'our', 'this',
    'that', 'from', 'have', 'has', 'was', 'were', 'can', 'able', 'who', 'not',
    'but', 'all', 'any', 'into', 'per', 'etc', 'use', 'using', 'work',
    'working', 'experience', 'knowledge', 'skills', 'skill', 'good', 'strong',
    'team', 'years', 'intern', 'internship', 'student', 'students', 'looking',
    'join', 'role', 'position', 'must', 'should', 'of', 'to', 'in', 'on', 'or',
    'as', 'at', 'by', 'is', 'it', 'be', 'we', 'an',
}
MIN_TEXT_SIM = 0.05


def tokenize(text):
    words = re.findall(r'[a-z0-9][a-z0-9+#.]*', (text or '').lower())
    tokens = []
    for w in words:
        w = w.rstrip('.')
        if len(w) > 1 and w not in STOPWORDS:
            tokens.append(w)
    return tokens


def parse_skills(text):
    """'Python, SQL; Docker' -> ['Python', 'SQL', 'Docker']"""
    skills, seen = [], set()
    for part in re.split(r'[,;\n•|]+', text or ''):
        skill = ' '.join(part.split()).strip(' -*').rstrip('.')
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            skills.append(skill)
    return skills


def has_skill(student_skill, requirement):
    """Whole-word match, so 'Java' does not match 'JavaScript'."""
    pattern = r'(?<![a-z0-9+#])' + re.escape(student_skill.lower().strip()) + r'(?![a-z0-9+#])'
    return re.search(pattern, requirement.lower()) is not None


def skill_match(student_skills, required):
    matched, missing = [], []
    for req in required:
        if any(has_skill(s, req) for s in student_skills):
            matched.append(req)
        else:
            missing.append(req)
    return matched, missing


def profile_text(profile):
    return ' '.join(filter(None, [profile.about_me, profile.experience, profile.education]))


def listing_tokens(listing):
    return (
        tokenize(listing.title) * 3
        + tokenize(getattr(listing, 'category', '')) * 2
        + tokenize(listing.required_skills) * 3
        + tokenize(listing.description)
    )


def build_idf(docs):
    n = len(docs)
    df = Counter()
    for tokens in docs:
        df.update(set(tokens))
    return {t: math.log((1 + n) / (1 + c)) + 1 for t, c in df.items()}


def vectorize(tokens, idf):
    return {t: count * idf.get(t, 1.0) for t, count in Counter(tokens).items()}


def cosine(a, b):
    common = set(a) & set(b)
    num = sum(a[t] * b[t] for t in common)
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return num / den if den else 0.0


def recommend(student_skills, text, listings, limit=6):
    """
    score = % of the internship's required skills the student has.
    Profile text similarity (TF-IDF cosine) breaks ties, and is the fallback
    for internships that list no skills.
    """
    listings = list(listings)
    if not listings:
        return []

    user_tokens = tokenize(text + ' ' + ' '.join(student_skills))
    docs = [listing_tokens(l) for l in listings]
    idf = build_idf(docs + [user_tokens])
    user_vec = vectorize(user_tokens, idf)

    results = []
    for listing, tokens in zip(listings, docs):
        required = parse_skills(listing.required_skills)
        matched, missing = skill_match(student_skills, required)
        text_sim = cosine(user_vec, vectorize(tokens, idf)) if user_tokens else 0.0

        if required:
            if not matched:
                continue
            score = round(100 * len(matched) / len(required))
        else:
            if text_sim < MIN_TEXT_SIM:
                continue
            score = round(text_sim * 100)

        results.append({
            'listing': listing,
            'score': score,
            'matched': matched,
            'missing': missing,
            'required_count': len(required),
            'text_sim': text_sim,
        })

    results.sort(key=lambda r: (r['score'], r['text_sim']), reverse=True)
    return results[:limit]