"""Tests for PII scrubbing utility."""
import pytest
from app.util.pii import redact_pii

@pytest.mark.parametrize("text,expected_counts", [
    ("Contact john.doe@example.com or +1 202-555-0187. SSN 123-45-6789", {"email":1, "phone":1, "ssn":1}),
    ("Multiple emails a@b.co c.d+tag@domain.io", {"email":2, "phone":0, "ssn":0}),
    ("No PII here", {"email":0, "phone":0, "ssn":0}),
])
def test_redact_pii_counts(text, expected_counts):
    redacted, counts = redact_pii(text)
    for k,v in expected_counts.items():
        assert counts[k] == v
    if expected_counts["email"]:
        assert "[REDACTED-EMAIL]" in redacted


def test_redact_pii_replaces_phone_and_ssn():
    text = "Phone 202-555-0187 and SSN 123-45-6789"
    redacted, counts = redact_pii(text)
    assert counts["phone"] == 1 and counts["ssn"] == 1
    assert "[REDACTED-PHONE]" in redacted and "[REDACTED-SSN]" in redacted
