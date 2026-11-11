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


def tokenize(text):
    words = re.findall(r'[a-z0-9][a-z0-9+#.]*', (text or '').lower())
    tokens = []
    for w in words:
        w = w.rstrip('.')
        if len(w) > 1 and w not in STOPWORDS:
            tokens.append(w)
    return tokens


def profile_text(profile):
    parts = []
    # Pull text from Lana's actual StudentProfile text fields
    for field in ['full_name', 'about_me', 'experience', 'education', 'nationality', 'language']:
        value = getattr(profile, field, None)
        if value:
            parts.append(str(value))
    
    # Pull skill names from Lana's related StudentSkill model relationship
    skills = [ss.skill.name for ss in profile.student_skills.all()]
    if skills:
        parts.append(' '.join(skills))
        
    return ' '.join(parts)


def listing_tokens(listing):
    # Title, category and requirements count more than the description.
    return (
        tokenize(listing.title) * 3
        + tokenize(listing.category) * 2
        + tokenize(listing.requirements) * 2
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


def recommend(text, listings, limit=5, min_score=0.01):
    """Return [{'listing', 'score' (0-100), 'matched' (keywords)}], best first."""
    listings = list(listings)
    user_tokens = tokenize(text)
    if not user_tokens or not listings:
        return []

    docs = [listing_tokens(l) for l in listings]
    idf = build_idf(docs + [user_tokens])
    user_vec = vectorize(user_tokens, idf)

    results = []
    for listing, tokens in zip(listings, docs):
        score = cosine(user_vec, vectorize(tokens, idf))
        
        # Check for actual keyword overlap to guarantee relevant matches get a boost
        matched = sorted(set(user_tokens) & set(tokens))
        
        if score < min_score and not matched:
            continue
            
        # Boost and normalize the score based on cosine similarity and shared keywords
        if matched:
            # Scale the raw cosine score, but guarantee a baseline minimum percentage (e.g. 45%+) if keywords match
            boosted_score = max(score * 600, len(matched) * 15 + 30)
            final_percentage = int(min(98, max(40, boosted_score)))
        else:
            final_percentage = int(score * 100)
            if final_percentage < min_score:
                continue

        results.append({
            'listing': listing,
            'score': final_percentage,
            'matched': matched[:6],
        })

    results.sort(key=lambda r: r['score'], reverse=True)
    return results[:limit]