"""PII scrubbing utilities for enterprise/government compliance."""
import re
from typing import Tuple

EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2}\d{4}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

REDACTIONS = {
    "email": "[REDACTED-EMAIL]",
    "phone": "[REDACTED-PHONE]",
    "ssn": "[REDACTED-SSN]",
}

def redact_pii(text: str) -> Tuple[str, dict[str, int]]:
    """Redact common PII (email, phone numbers, SSNs) returning redacted text and counts.

    Args:
        text: Input text possibly containing PII.
    Returns:
        (redacted_text, counts) where counts maps type->number removed.
    """
    counts = {"email": 0, "phone": 0, "ssn": 0}

    def _sub(pattern: re.Pattern, label: str, replacement: str, data: str) -> str:
        def _repl(match: re.Match) -> str:
            counts[label] += 1
            return replacement
        return pattern.sub(_repl, data)

    redacted = text
    redacted = _sub(EMAIL_PATTERN, "email", REDACTIONS["email"], redacted)
    redacted = _sub(PHONE_PATTERN, "phone", REDACTIONS["phone"], redacted)
    redacted = _sub(SSN_PATTERN, "ssn", REDACTIONS["ssn"], redacted)

    return redacted, counts

__all__ = ["redact_pii"]
