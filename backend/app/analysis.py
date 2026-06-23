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


def extract_skills(text: str) -> list[str]:
    return sorted(_extract_skills(text))


def build_recruiter_summary(
    resume_text: str,
    job_description: str,
    match_score: int,
    missing_skills: list[str],
    language: str = "en",
) -> dict[str, Any]:
    resume_skills = _extract_skills(resume_text)
    job_skills = _extract_skills(job_description)
    strongest_skills = sorted(resume_skills & job_skills)
    concerns = []
    if missing_skills:
        concerns.append("Skill gaps to validate: " + ", ".join(missing_skills[:5]) + ".")
    if match_score < 70:
        concerns.append("Resume evidence may not be targeted enough for this job post.")
    if not concerns:
        concerns.append("No major concerns from the resume text; validate depth during screening.")

    if match_score >= 80:
        recommendation = "Strong fit"
    elif match_score >= 55:
        recommendation = "Possible fit"
    else:
        recommendation = "Weak fit"

    questions = []
    for skill in (missing_skills[:3] or strongest_skills[:3] or ["this role"]):
        questions.append(f"Can you describe a recent project where you used or learned {skill}?")
    questions.append("What measurable outcome from your resume best maps to this job?")

    resume_summary = "Candidate resume mentions " + (", ".join(strongest_skills[:6]) if strongest_skills else "transferable experience") + "."
    good_fit = "Matches key role signals: " + (", ".join(strongest_skills[:6]) if strongest_skills else "general experience and project history") + "."
    if language == "es":
        concerns = []
        if missing_skills:
            concerns.append("Brechas de habilidades para validar: " + ", ".join(missing_skills[:5]) + ".")
        if match_score < 70:
            concerns.append("La evidencia del resume puede no estar suficientemente alineada con este puesto.")
        if not concerns:
            concerns.append("No hay preocupaciones principales en el texto del resume; valida profundidad en la entrevista.")
        questions = []
        for skill in (missing_skills[:3] or strongest_skills[:3] or ["este puesto"]):
            questions.append(f"Describe un proyecto reciente donde usaste o aprendiste {skill}.")
        questions.append("Que resultado medible de tu resume se conecta mejor con este puesto?")
        resume_summary = "El resume menciona " + (", ".join(strongest_skills[:6]) if strongest_skills else "experiencia transferible") + "."
        good_fit = "Coincide con senales clave del puesto: " + (", ".join(strongest_skills[:6]) if strongest_skills else "experiencia general e historial de proyectos") + "."

    return {
        "strongest_skills": strongest_skills,
        "resume_summary": resume_summary,
        "fit_summary": good_fit,
        "concerns": concerns,
        "interview_questions": questions,
        "recommendation": recommendation,
    }


def heuristic_analysis(resume_text: str, job_description: str, language: str = "en") -> dict[str, Any]:
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
    if language == "es":
        if missing:
            improvements.append("Agrega ejemplos concretos que demuestren experiencia con: " + ", ".join(missing[:6]) + ".")
        improvements.append("Usa lenguaje parecido al job post cuando refleje tu experiencia real.")
        improvements.append("Agrega resultados medibles como ingresos, tiempo ahorrado, precision, latencia o adopcion.")
        improvements.append("Mueve las habilidades y proyectos mas relevantes al primer tercio del resume.")
        summary = "Analisis local completado porque no hay una API key de OpenAI configurada."
    else:
        if missing:
            improvements.append("Add concrete examples that show experience with: " + ", ".join(missing[:6]) + ".")
        improvements.append("Mirror the job description language where it accurately reflects your experience.")
        improvements.append("Add measurable outcomes such as revenue, time saved, accuracy, latency, or adoption.")
        improvements.append("Move the most relevant skills and projects into the top third of the resume.")
        summary = "Heuristic analysis completed locally because no OpenAI API key was configured."

    return {
        "match_score": max(0, min(100, score)),
        "missing_skills": missing,
        "strongest_skills": sorted(resume_skills & job_skills),
        "improvements": improvements,
        "summary": summary,
        "source": "heuristic",
    }


def ai_analysis(settings: Settings, resume_text: str, job_description: str, language: str = "en") -> dict[str, Any]:
    if not settings.openai_api_key or settings.openai_api_key == "your_api_key_here":
        return heuristic_analysis(resume_text, job_description, language=language)

    client = OpenAI(api_key=settings.openai_api_key)
    language_name = "Spanish" if language == "es" else "English"
    prompt = {
        "role": "user",
        "content": (
            "Analyze this resume against the job description. Return strict JSON with keys "
            "match_score (integer 0-100), missing_skills (array of strings), improvements "
            f"(array of strings), and summary (short string). Write user-facing text in {language_name}.\n\n"
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
        data["strongest_skills"] = extract_skills(resume_text)
        data["improvements"] = list(data.get("improvements", []))
        data["summary"] = str(data.get("summary", ""))
        data["source"] = "openai"
        return data
    except (OpenAIError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        fallback = heuristic_analysis(resume_text, job_description, language=language)
        fallback["summary"] = (
            "OpenAI fallo, asi que se uso un analisis local."
            if language == "es"
            else "OpenAI analysis failed, so a local heuristic analysis was used."
        )
        return fallback
