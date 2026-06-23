import hashlib
import hmac
import base64
import json
import re
import time
from typing import Optional
from urllib.parse import urlparse


FAKE_EMAIL_DOMAINS = {"test.com", "fake.com", "example.invalid", "mailinator.com", "tempmail.com"}
PHONE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_access_token(user_id: int, secret: str, expires_in_seconds: int = 60 * 60 * 24 * 7) -> str:
    payload = {"sub": user_id, "exp": int(time.time()) + expires_in_seconds}
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
    return f"{payload_b64}.{signature_b64}"


def verify_access_token(token: str, secret: str) -> Optional[int]:
    try:
        payload_b64, signature_b64 = token.split(".", 1)
        expected = hmac.new(secret.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).digest()
        actual = base64.urlsafe_b64decode(signature_b64 + "=" * (-len(signature_b64) % 4))
        if not hmac.compare_digest(expected, actual):
            return None
        payload_raw = base64.urlsafe_b64decode(payload_b64 + "=" * (-len(payload_b64) % 4))
        payload = json.loads(payload_raw)
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return int(payload["sub"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def is_valid_email(email: str) -> bool:
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False
    domain = email.rsplit("@", 1)[-1].lower()
    if domain in FAKE_EMAIL_DOMAINS:
        return False
    if domain.endswith(".test") or domain.endswith(".invalid"):
        return False
    return True


def is_valid_phone_number(phone_number: str) -> bool:
    return bool(PHONE_PATTERN.fullmatch(phone_number.strip()))


def is_valid_website(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and "." in parsed.netloc


def domain_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower()


def company_email_matches_website(email: str, website: str) -> bool:
    if not email or not website or not is_valid_email(email) or not is_valid_website(website):
        return False
    company_domain = domain_from_url(website)
    return email_domain(email) == company_domain or email_domain(email).endswith("." + company_domain)
