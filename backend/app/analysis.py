import json
import re
from typing import Any

from openai import OpenAI, OpenAIError

from .config import Settings


COMMON_SKILLS = {
    "python",
    "javascript",
    "typescript",
    "react",
    "next.js",
    "node",
    "fastapi",
    "django",
    "flask",
    "sql",
    "sqlite",
    "postgresql",
    "mysql",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "terraform",
    "git",
    "github actions",
    "ci/cd",
    "machine learning",
    "nlp",
    "openai",
    "rest api",
    "graphql",
    "pytest",
    "jest",
    "tailwind",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _extract_skills(text: str) -> set[str]:
    normalized = _normalize(text)
    return {skill for skill in COMMON_SKILLS if skill in normalized}


def heuristic_analysis(resume_text: str, job_description: str) -> dict[str, Any]:
    resume_skills = _extract_skills(resume_text)
    job_skills = _extract_skills(job_description)
    missing = sorted(job_skills - resume_skills)
    overlap = len(resume_skills & job_skills)

    if job_skills:
        score = round((overlap / len(job_skills)) * 100)
    else:
        resume_words = set(re.findall(r"[a-zA-Z][a-zA-Z+#.-]{2,}", _normalize(resume_text)))
        job_words = set(re.findall(r"[a-zA-Z][a-zA-Z+#.-]{2,}", _normalize(job_description)))
        score = round((len(resume_words & job_words) / max(len(job_words), 1)) * 100)

    improvements = []
    if missing:
        improvements.append("Add concrete examples that show experience with: " + ", ".join(missing[:6]) + ".")
    improvements.append("Mirror the job description language where it accurately reflects your experience.")
    improvements.append("Add measurable outcomes such as revenue, time saved, accuracy, latency, or adoption.")
    improvements.append("Move the most relevant skills and projects into the top third of the resume.")

    return {
        "match_score": max(0, min(100, score)),
        "missing_skills": missing,
        "improvements": improvements,
        "summary": "Heuristic analysis completed locally because no OpenAI API key was configured.",
        "source": "heuristic",
    }


def ai_analysis(settings: Settings, resume_text: str, job_description: str) -> dict[str, Any]:
    if not settings.openai_api_key or settings.openai_api_key == "your_api_key_here":
        return heuristic_analysis(resume_text, job_description)

    client = OpenAI(api_key=settings.openai_api_key)
    prompt = {
        "role": "user",
        "content": (
            "Analyze this resume against the job description. Return strict JSON with keys "
            "match_score (integer 0-100), missing_skills (array of strings), improvements "
            "(array of strings), and summary (short string).\n\n"
            f"Resume:\n{resume_text}\n\nJob description:\n{job_description}"
        ),
    }
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise hiring analyst. Output only valid JSON.",
                },
                prompt,
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        data["match_score"] = max(0, min(100, int(data.get("match_score", 0))))
        data["missing_skills"] = list(data.get("missing_skills", []))
        data["improvements"] = list(data.get("improvements", []))
        data["summary"] = str(data.get("summary", ""))
        data["source"] = "openai"
        return data
    except (OpenAIError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        fallback = heuristic_analysis(resume_text, job_description)
        fallback["summary"] = "OpenAI analysis failed, so a local heuristic analysis was used."
        return fallback
