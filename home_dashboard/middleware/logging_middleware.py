"""Logging middleware with sensitive data redaction."""

import re

# Sensitive parameters to redact from URLs
SENSITIVE_PARAMS = [
    "appid",
    "api_key",
    "token",
    "password",
    "secret",
    "key",
    "refresh_token",
    "access_token",
    "client_secret",
    "auth_token",
    "authorization",
    "bearer",
]


def redact_sensitive_data(url: str) -> str:
    """Redact sensitive query parameters from URL."""
    redacted = url
    for param in SENSITIVE_PARAMS:
        pattern = rf"{param}=([^&\s\"]+)"
        redacted = re.sub(pattern, f"{param}=***REDACTED***", redacted)
    return redacted
