"""PII redaction middleware for logging/telemetry.

Wraps agent-framework's middleware hooks (request/response processing) to
strip fields that must never be persisted or logged: raw bill uploads,
exact street address, account numbers. Wire into each Agent's middleware
list once the LLM client is configured.

Never store real utility bill uploads - only synthetic/example tariff
profiles are used in this project (see data/tariff_profiles.json).
"""
from __future__ import annotations

import re

_PII_FIELD_NAMES = {"utility_bill", "account_number", "street_address", "ssn"}
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")


def redact_dict(payload: dict) -> dict:
    """Remove/mask known-sensitive fields before logging or persisting."""
    redacted = {}
    for key, value in payload.items():
        if key.lower() in _PII_FIELD_NAMES:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, str):
            redacted[key] = redact_text(value)
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value)
        else:
            redacted[key] = value
    return redacted


def redact_text(text: str) -> str:
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _PHONE_RE.sub("[REDACTED_PHONE]", text)
    return text


async def logging_middleware(context, next_handler):
    """Example agent-framework style middleware: redact before logging.

    Actual signature depends on the installed agent-framework version's
    middleware API (request/response interceptor) - adapt when wiring into
    Agent(..., middleware=[logging_middleware]).
    """
    if hasattr(context, "arguments"):
        context.arguments = redact_dict(dict(context.arguments))
    result = await next_handler(context)
    return result
