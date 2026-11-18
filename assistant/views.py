import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .services import AssistantError, ask_assistant

HISTORY_KEY = "assistant_history"


def _error(message, status):
    return JsonResponse({"error": message}, status=status)


def _is_rate_limited(user_id):
    """Allow at most AI_RATE_LIMIT_PER_MINUTE questions per user per minute."""
    key = f"assistant:rate:{user_id}"
    if cache.add(key, 1, timeout=60):
        return False
    try:
        count = cache.incr(key)
    except ValueError:            # key expired between add() and incr()
        cache.set(key, 1, timeout=60)
        return False
    return count > settings.AI_RATE_LIMIT_PER_MINUTE


@login_required
def chat_view(request):
    history = request.session.get(HISTORY_KEY, [])
    return render(request, "assistant/chat.html", {
        "history": history,
        "max_length": settings.AI_MAX_QUESTION_LENGTH,
    })


@login_required
@require_POST
def ask_view(request):
    try:
        payload = json.loads(request.body or b"{}")
    except (ValueError, UnicodeDecodeError):
        return _error("Invalid request.", 400)
    if not isinstance(payload, dict) or not isinstance(payload.get("message"), str):
        return _error("Invalid request.", 400)

    message = payload["message"].strip()
    if not message:
        return _error("Please type a question.", 400)
    if len(message) > settings.AI_MAX_QUESTION_LENGTH:
        return _error(
            f"Your question is too long (max {settings.AI_MAX_QUESTION_LENGTH} characters).", 400)

    if _is_rate_limited(request.user.id):
        return _error("You're asking too fast. Please wait a moment and try again.", 429)

    history = request.session.get(HISTORY_KEY, [])
    try:
        reply = ask_assistant(request.user, message, history)
    except AssistantError as error:
        return _error(error.message, error.status)

    history = history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply},
    ]
    request.session[HISTORY_KEY] = history[-settings.AI_HISTORY_LIMIT:]
    return JsonResponse({"reply": reply})


@login_required
@require_POST
def clear_view(request):
    request.session.pop(HISTORY_KEY, None)
    return JsonResponse({"ok": True})