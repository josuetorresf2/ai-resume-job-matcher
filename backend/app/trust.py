import re


SCAM_PHRASES = [
    "wire transfer",
    "crypto payment",
    "no experience needed earn",
    "pay to apply",
    "whatsapp only",
    "telegram only",
    "guaranteed income",
    "send money",
]


def repeated_text_score(text: str) -> int:
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0
    unique_ratio = len(set(words)) / len(words)
    return 25 if unique_ratio < 0.35 and len(words) > 30 else 0


def assess_job_safety(description: str, company_complete: bool) -> tuple[int, list[str]]:
    reasons = []
    text = description.lower()
    link_count = len(re.findall(r"https?://|www\.", text))
    if link_count > 2:
        reasons.append("Too many links in the job description.")
    if re.search(r"\$\d{4,}.*(day|week)|earn.*\$\d{4,}", text):
        reasons.append("Suspicious salary promise detected.")
    if repeated_text_score(description):
        reasons.append("Repeated text makes the post look spammy.")
    if not company_complete:
        reasons.append("Company profile is incomplete.")
    if len(description.strip()) < 120:
        reasons.append("Job description is too short.")
    for phrase in SCAM_PHRASES:
        if phrase in text:
            reasons.append(f"Scam-like phrase detected: {phrase}.")

    score = min(100, len(reasons) * 22 + link_count * 8 + repeated_text_score(description))
    return score, reasons


def assess_job_quality(
    title: str,
    description: str,
    required_skills: str,
    salary_range: str,
    company_complete: bool,
    spam_score: int,
) -> tuple[int, list[str]]:
    tips = []
    text = description.lower()
    score = 100
    if len(title.strip()) < 5:
        score -= 15
        tips.append("Use a clear job title.")
    if not any(word in text for word in ["responsibilities", "you will", "role", "build", "manage", "support"]):
        score -= 15
        tips.append("Add clear responsibilities.")
    if not required_skills.strip():
        score -= 15
        tips.append("List required skills.")
    if not salary_range.strip():
        score -= 10
        tips.append("Add transparent salary information.")
    if not company_complete:
        score -= 15
        tips.append("Complete and verify the company profile.")
    if spam_score > 0:
        score -= min(30, spam_score // 2)
        tips.append("Remove scam or spam signals before publishing.")
    if not any(word in text for word in ["inclusive", "equal opportunity", "welcome", "accessibility", "accommodation"]):
        score -= 5
        tips.append("Add inclusive language.")
    return max(0, min(100, score)), tips


def candidate_completeness_score(has_resume: bool, skills: str, experience: str, education: str, links: list[str], language: str) -> int:
    score = 0
    score += 25 if has_resume else 0
    score += 20 if skills.strip() else 0
    score += 15 if experience.strip() else 0
    score += 15 if education.strip() else 0
    score += 15 if any(link.strip() for link in links) else 0
    score += 10 if language else 0
    return score


def recruiter_trust_score(email_verified: bool, company_verified: bool, company_complete: bool, low_spam_jobs: bool) -> int:
    score = 0
    score += 25 if email_verified else 0
    score += 35 if company_verified else 0
    score += 20 if company_complete else 0
    score += 10 if low_spam_jobs else 0
    score += 5  # response rate placeholder
    score += 5  # no reports placeholder
    return score
