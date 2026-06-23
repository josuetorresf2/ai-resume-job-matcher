import hashlib
import re
from urllib.parse import urlparse


FAKE_EMAIL_DOMAINS = {"test.com", "fake.com", "example.invalid", "mailinator.com", "tempmail.com"}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_valid_email(email: str) -> bool:
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return False
    domain = email.rsplit("@", 1)[-1].lower()
    if domain in FAKE_EMAIL_DOMAINS:
        return False
    if domain.endswith(".test") or domain.endswith(".invalid"):
        return False
    return True


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
