export type Analysis = {
  id: number;
  match_score: number;
  missing_skills: string[];
  improvements: string[];
  summary: string;
  created_at: string;
  source: string;
  resume_text?: string;
  job_description?: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function createAnalysis(resumeText: string, jobDescription: string): Promise<Analysis> {
  const response = await fetch(`${API_URL}/analyses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text: resumeText, job_description: jobDescription }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Could not analyze resume.");
  }

  return response.json();
}

export async function listAnalyses(): Promise<Analysis[]> {
  const response = await fetch(`${API_URL}/analyses`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Could not load analysis history.");
  }
  return response.json();
}

export async function extractResumeText(file: File): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/resume-text`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Could not read that resume file. Use a UTF-8 .txt file.");
  }

  const payload = await response.json();
  return payload.text;
}
