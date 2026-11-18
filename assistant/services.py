import logging

import openai
from django.conf import settings
from openai import OpenAI

from .prompts import build_system_prompt
from .tools import run_tool, tools_for_role

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3
FALLBACK_REPLY = "Sorry, I couldn't come up with an answer. Please try rephrasing your question."


class AssistantError(Exception):
    """An error whose message is safe to show to the user."""

    def __init__(self, message, status=502):
        super().__init__(message)
        self.message = message
        self.status = status


def get_client():
    return OpenAI(
        api_key=settings.AI_API_KEY,
        base_url=settings.AI_BASE_URL,
        timeout=settings.AI_TIMEOUT,
        max_retries=1,
    )


def _clean_history(history):
    """Keep only well-formed user/assistant text messages."""
    cleaned = []
    for item in history or []:
        if (isinstance(item, dict)
                and item.get("role") in ("user", "assistant")
                and isinstance(item.get("content"), str)):
            cleaned.append({"role": item["role"], "content": item["content"]})
    return cleaned[-settings.AI_HISTORY_LIMIT:]


def _call_model(client, messages, tools):
    kwargs = {
        "model": settings.AI_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": settings.AI_MAX_TOKENS,
    }
    if tools:
        kwargs["tools"] = tools
    try:
        return client.chat.completions.create(**kwargs)
    except openai.BadRequestError:
        # Free models sometimes produce a malformed tool call. Retry without tools.
        if not tools:
            raise
        logger.warning("Tool call rejected by the model; retrying without tools")
        kwargs.pop("tools")
        return client.chat.completions.create(**kwargs)


def ask_assistant(user, question, history=None):
    """Send the question to the AI (running tools if it asks) and return its reply."""
    if not settings.AI_API_KEY:
        raise AssistantError(
            "The assistant is not set up yet. Please contact the administrator.", 503)

    messages = (
        [{"role": "system", "content": build_system_prompt(user)}]
        + _clean_history(history)
        + [{"role": "user", "content": question}]
    )
    tools = tools_for_role(user.role)

    try:
        client = get_client()
        for round_number in range(MAX_TOOL_ROUNDS + 1):
            # On the last round, offer no tools so the AI must answer in text.
            round_tools = tools if round_number < MAX_TOOL_ROUNDS else None
            response = _call_model(client, messages, round_tools)
            if not response.choices:
                return FALLBACK_REPLY
            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None)

            if not tool_calls:
                return (message.content or "").strip() or FALLBACK_REPLY

            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {"id": c.id, "type": "function",
                     "function": {"name": c.function.name,
                                  "arguments": c.function.arguments}}
                    for c in tool_calls
                ],
            })
            for call in tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": run_tool(call.function.name, call.function.arguments, user),
                })
        return FALLBACK_REPLY

    except openai.APITimeoutError:
        raise AssistantError("The assistant took too long to answer. Please try again.", 504)
    except openai.APIConnectionError:
        raise AssistantError("Couldn't reach the AI service. Check your connection and try again.", 503)
    except openai.AuthenticationError:
        logger.error("AI API key was rejected")
        raise AssistantError("The assistant is not set up correctly. Please contact the administrator.", 503)
    except openai.RateLimitError:
        raise AssistantError("The assistant is busy right now. Please try again in a minute.", 503)
    except openai.APIStatusError:
        logger.exception("AI API returned an error")
        raise AssistantError("The assistant ran into a problem. Please try again.", 502)