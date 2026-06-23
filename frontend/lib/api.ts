export type Role = "candidate" | "recruiter";

export type User = {
  id: number;
  name: string;
  email: string;
  role: Role;
};

export type CandidateProfile = {
  id: number;
  user_id: number;
  headline: string;
  skills: string;
  bio: string;
};

export type RecruiterProfile = {
  id: number;
  user_id: number;
  company: string;
  title: string;
};

export type Resume = {
  id: number;
  candidate_user_id: number;
  title: string;
  resume_text: string;
  created_at: string;
  updated_at: string;
};

export type JobPost = {
  id: number;
  recruiter_user_id: number;
  title: string;
  company: string;
  location: string;
  work_mode: "remote" | "hybrid" | "onsite";
  salary_range: string;
  experience_level: string;
  required_skills: string;
  nice_to_have_skills: string;
  description: string;
  created_at: string;
  updated_at: string;
};

export type JobDashboardItem = JobPost & {
  candidates_matched: number;
  average_match_score: number;
  shortlisted_count: number;
};

export type RecruiterDashboard = {
  job_posts: JobDashboardItem[];
  total_shortlisted: number;
};

export type Analysis = {
  id: number;
  resume_id?: number | null;
  job_post_id?: number | null;
  candidate_user_id?: number | null;
  recruiter_user_id?: number | null;
  match_score: number;
  missing_skills: string[];
  strongest_skills: string[];
  improvements: string[];
  summary: string;
  resume_summary: string;
  fit_summary: string;
  concerns: string[];
  interview_questions: string[];
  recommendation: string;
  recruiter_status?: "Shortlisted" | "Maybe" | "Rejected" | null;
  recruiter_notes?: string | null;
  created_at: string;
  source: string;
  resume_text?: string;
  job_description?: string;
};

export type RankedCandidateMatch = Analysis & {
  candidate_name: string;
  candidate_headline: string;
  resume_title: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function sessionHeaders(user?: User | null): HeadersInit {
  return user ? { "Content-Type": "application/json", "X-User-Id": String(user.id) } : { "Content-Type": "application/json" };
}

function humanizeErrorDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === "string") return item;
        if (item && typeof item === "object" && "msg" in item) return String(item.msg);
        return JSON.stringify(item);
      })
      .join(" ");
  }
  if (detail && typeof detail === "object") {
    if ("message" in detail) return String(detail.message);
    if ("msg" in detail) return String(detail.msg);
    return JSON.stringify(detail);
  }
  return fallback;
}

async function parseResponse<T>(response: Response, fallback: string): Promise<T> {
  if (response.ok) return response.json();
  let message = fallback;
  try {
    const payload = await response.json();
    message = humanizeErrorDetail(payload.detail, fallback);
  } catch {
    message = await response.text();
  }
  throw new Error(message || fallback);
}

export async function mockLogin(name: string, email: string, role: Role): Promise<User> {
  const response = await fetch(`${API_URL}/auth/mock-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, role }),
  });
  return parseResponse<User>(response, "Could not start mock session.");
}

export async function getCandidateProfile(user: User): Promise<CandidateProfile> {
  const response = await fetch(`${API_URL}/candidate/profile`, { headers: sessionHeaders(user), cache: "no-store" });
  return parseResponse<CandidateProfile>(response, "Could not load candidate profile.");
}

export async function saveCandidateProfile(user: User, profile: Omit<CandidateProfile, "id" | "user_id">): Promise<CandidateProfile> {
  const response = await fetch(`${API_URL}/candidate/profile`, {
    method: "PUT",
    headers: sessionHeaders(user),
    body: JSON.stringify(profile),
  });
  return parseResponse<CandidateProfile>(response, "Could not save candidate profile.");
}

export async function getRecruiterProfile(user: User): Promise<RecruiterProfile> {
  const response = await fetch(`${API_URL}/recruiter/profile`, { headers: sessionHeaders(user), cache: "no-store" });
  return parseResponse<RecruiterProfile>(response, "Could not load recruiter profile.");
}

export async function saveRecruiterProfile(user: User, profile: Omit<RecruiterProfile, "id" | "user_id">): Promise<RecruiterProfile> {
  const response = await fetch(`${API_URL}/recruiter/profile`, {
    method: "PUT",
    headers: sessionHeaders(user),
    body: JSON.stringify(profile),
  });
  return parseResponse<RecruiterProfile>(response, "Could not save recruiter profile.");
}

export async function createResume(user: User, title: string, resumeText: string): Promise<Resume> {
  const response = await fetch(`${API_URL}/resumes`, {
    method: "POST",
    headers: sessionHeaders(user),
    body: JSON.stringify({ title, resume_text: resumeText }),
  });
  return parseResponse<Resume>(response, "Could not save resume.");
}

export async function updateResume(user: User, resumeId: number, title: string, resumeText: string): Promise<Resume> {
  const response = await fetch(`${API_URL}/resumes/${resumeId}`, {
    method: "PUT",
    headers: sessionHeaders(user),
    body: JSON.stringify({ title, resume_text: resumeText }),
  });
  return parseResponse<Resume>(response, "Could not update resume.");
}

export async function listResumes(user: User): Promise<Resume[]> {
  const response = await fetch(`${API_URL}/resumes`, { headers: sessionHeaders(user), cache: "no-store" });
  return parseResponse<Resume[]>(response, "Could not load resumes.");
}

export type JobPostInput = {
  title: string;
  company: string;
  location: string;
  work_mode: "remote" | "hybrid" | "onsite";
  salary_range: string;
  experience_level: string;
  required_skills: string;
  nice_to_have_skills: string;
  description: string;
};

export async function createJobPost(user: User, input: JobPostInput): Promise<JobPost> {
  const response = await fetch(`${API_URL}/job-posts`, {
    method: "POST",
    headers: sessionHeaders(user),
    body: JSON.stringify(input),
  });
  return parseResponse<JobPost>(response, "Could not save job post.");
}

export async function updateJobPost(user: User, jobPostId: number, input: JobPostInput): Promise<JobPost> {
  const response = await fetch(`${API_URL}/job-posts/${jobPostId}`, {
    method: "PUT",
    headers: sessionHeaders(user),
    body: JSON.stringify(input),
  });
  return parseResponse<JobPost>(response, "Could not update job post.");
}

export async function deleteJobPost(user: User, jobPostId: number): Promise<void> {
  const response = await fetch(`${API_URL}/job-posts/${jobPostId}`, {
    method: "DELETE",
    headers: sessionHeaders(user),
  });
  await parseResponse<{ status: string }>(response, "Could not delete job post.");
}

export async function listJobPosts(): Promise<JobPost[]> {
  const response = await fetch(`${API_URL}/job-posts`, { cache: "no-store" });
  return parseResponse<JobPost[]>(response, "Could not load job posts.");
}

export async function listMyJobPosts(user: User): Promise<JobPost[]> {
  const response = await fetch(`${API_URL}/job-posts/mine`, { headers: sessionHeaders(user), cache: "no-store" });
  return parseResponse<JobPost[]>(response, "Could not load your job posts.");
}

export async function getRecruiterDashboard(user: User): Promise<RecruiterDashboard> {
  const response = await fetch(`${API_URL}/recruiter/dashboard`, { headers: sessionHeaders(user), cache: "no-store" });
  return parseResponse<RecruiterDashboard>(response, "Could not load recruiter dashboard.");
}

export async function listRankedCandidates(user: User, jobPostId: number): Promise<RankedCandidateMatch[]> {
  const response = await fetch(`${API_URL}/job-posts/${jobPostId}/ranked-candidates`, { headers: sessionHeaders(user), cache: "no-store" });
  return parseResponse<RankedCandidateMatch[]>(response, "Could not load ranked candidates.");
}

export async function updateMatchReview(
  user: User,
  analysisId: number,
  recruiterStatus: "Shortlisted" | "Maybe" | "Rejected",
  recruiterNotes: string,
): Promise<Analysis> {
  const response = await fetch(`${API_URL}/matches/${analysisId}/review`, {
    method: "PUT",
    headers: sessionHeaders(user),
    body: JSON.stringify({ recruiter_status: recruiterStatus, recruiter_notes: recruiterNotes }),
  });
  return parseResponse<Analysis>(response, "Could not update candidate review.");
}

export async function createMatch(user: User, resumeId: number, jobPostId: number): Promise<Analysis> {
  const response = await fetch(`${API_URL}/matches`, {
    method: "POST",
    headers: sessionHeaders(user),
    body: JSON.stringify({ resume_id: resumeId, job_post_id: jobPostId }),
  });
  return parseResponse<Analysis>(response, "Could not analyze match.");
}

export async function listMatches(user: User): Promise<Analysis[]> {
  const response = await fetch(`${API_URL}/matches`, { headers: sessionHeaders(user), cache: "no-store" });
  return parseResponse<Analysis[]>(response, "Could not load match history.");
}

export async function createAnalysis(resumeText: string, jobDescription: string): Promise<Analysis> {
  const response = await fetch(`${API_URL}/analyses`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ resume_text: resumeText, job_description: jobDescription }),
  });
  return parseResponse<Analysis>(response, "Could not analyze resume.");
}

export async function extractResumeText(file: File): Promise<string> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_URL}/resume-text`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Could not read that resume file. Use a UTF-8 .txt file or readable PDF.");
  }

  const payload = await response.json();
  return payload.text;
}
