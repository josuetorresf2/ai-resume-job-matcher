"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Analysis,
  CandidateProfile,
  JobDashboardItem,
  JobPostInput,
  JobPost,
  RankedCandidateMatch,
  RecruiterProfile,
  Resume,
  Role,
  User,
  createJobPost,
  createMatch,
  createResume,
  deleteJobPost,
  extractResumeText,
  getCandidateProfile,
  getRecruiterProfile,
  getRecruiterDashboard,
  listRankedCandidates,
  listJobPosts,
  listMatches,
  listMyJobPosts,
  listResumes,
  mockLogin,
  saveCandidateProfile,
  saveRecruiterProfile,
  updateMatchReview,
  updateJobPost,
  updateResume,
} from "../lib/api";
import { scoreLabel, scoreTone } from "../lib/score";

const sampleResume =
  "Full-stack developer with Python, FastAPI, React, SQL, Docker, Git, and REST API experience. Built dashboards and automated workflows for internal teams.";
const sampleJob =
  "Hiring a software engineer with Python, FastAPI, React, Docker, SQL, AWS, GitHub Actions, and experience building production REST APIs.";

export default function Home() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [role, setRole] = useState<Role | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  async function onLogin(selectedRole: Role) {
    setError("");
    setLoading(true);
    try {
      const safeName = name || (selectedRole === "candidate" ? "Demo Candidate" : "Demo Recruiter");
      const safeEmail = email || `${selectedRole}-${Date.now()}@example.com`;
      const session = await mockLogin(safeName, safeEmail, selectedRole);
      setRole(session.role);
      setUser(session);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start session.");
    } finally {
      setLoading(false);
    }
  }

  function resetSession() {
    setUser(null);
    setRole(null);
    setError("");
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Role-based matching workspace</p>
          <h1>AI Resume & Job Matcher</h1>
          <p className="subtitle">Separate candidate and recruiter workflows with ownership checks around resumes, job posts, and match results.</p>
        </div>
        <div className="topbar-actions">
          <button className="theme-toggle" onClick={() => setTheme((value) => (value === "dark" ? "light" : "dark"))}>
            {theme === "dark" ? "Light mode" : "Dark mode"}
          </button>
          {user ? <button className="theme-toggle" onClick={resetSession}>Switch role</button> : null}
          <div className="status-pill">{user ? `${user.name} · ${user.role}` : "Mock session auth"}</div>
        </div>
      </header>

      {!user || !role ? (
        <RoleSelection name={name} email={email} error={error} loading={loading} setName={setName} setEmail={setEmail} onLogin={onLogin} />
      ) : role === "candidate" ? (
        <CandidateDashboard user={user} />
      ) : (
        <RecruiterDashboard user={user} />
      )}
    </main>
  );
}

function RoleSelection({
  name,
  email,
  error,
  loading,
  setName,
  setEmail,
  onLogin,
}: {
  name: string;
  email: string;
  error: string;
  loading: boolean;
  setName: (value: string) => void;
  setEmail: (value: string) => void;
  onLogin: (role: Role) => Promise<void>;
}) {
  const canLogin = !loading;

  return (
    <section className="role-grid">
      <div className="panel role-panel">
        <div className="panel-header">
          <div>
            <h2>Choose your workspace</h2>
            <p>This mock login creates a session user and applies role-based route permissions.</p>
          </div>
        </div>
        <label className="field">
          <span>Name</span>
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Alex Morgan" />
        </label>
        <label className="field">
          <span>Email</span>
          <input value={email} onChange={(event) => setEmail(event.target.value)} placeholder="alex@example.com" />
        </label>
        {error ? (
          <div className="error" role="alert">
            <strong>Session issue</strong>
            <span>{error}</span>
          </div>
        ) : null}
        <div className="role-actions">
          <button className="primary-action" disabled={!canLogin} onClick={() => onLogin("recruiter")}>
            I am a Recruiter
          </button>
          <button className="secondary-action" disabled={!canLogin} onClick={() => onLogin("candidate")}>
            I am a Candidate
          </button>
        </div>
      </div>
      <div className="panel permissions-panel">
        <h2>Permission model</h2>
        <div className="permission-list">
          <div>
            <strong>Candidate</strong>
            <p>Can edit their own profile and resumes, run matches against job posts, and view their own match history.</p>
          </div>
          <div>
            <strong>Recruiter</strong>
            <p>Can edit their own profile and job posts, view match results tied to their jobs, and cannot modify candidate resumes.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function CandidateDashboard({ user }: { user: User }) {
  const [profile, setProfile] = useState<CandidateProfile>({ id: 0, user_id: user.id, headline: "", skills: "", bio: "" });
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<JobPost[]>([]);
  const [matches, setMatches] = useState<Analysis[]>([]);
  const [resumeId, setResumeId] = useState("");
  const [jobPostId, setJobPostId] = useState("");
  const [resumeTitle, setResumeTitle] = useState("Primary resume");
  const [resumeText, setResumeText] = useState(sampleResume);
  const [current, setCurrent] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    refreshCandidate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id]);

  async function refreshCandidate() {
    setError("");
    try {
      const [nextProfile, nextResumes, nextJobs, nextMatches] = await Promise.all([
        getCandidateProfile(user),
        listResumes(user),
        listJobPosts(),
        listMatches(user),
      ]);
      setProfile(nextProfile);
      setResumes(nextResumes);
      setJobs(nextJobs);
      setMatches(nextMatches);
      setCurrent(nextMatches[0] ?? null);
      setResumeId(nextResumes[0] ? String(nextResumes[0].id) : "");
      setJobPostId(nextJobs[0] ? String(nextJobs[0].id) : "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load candidate workspace.");
    }
  }

  async function onSaveProfile() {
    setNotice("");
    setError("");
    const saved = await saveCandidateProfile(user, { headline: profile.headline, skills: profile.skills, bio: profile.bio });
    setProfile(saved);
    setNotice("Candidate profile saved.");
  }

  async function onSaveResume() {
    setNotice("");
    setError("");
    setLoading(true);
    try {
      const saved = resumeId
        ? await updateResume(user, Number(resumeId), resumeTitle, resumeText)
        : await createResume(user, resumeTitle, resumeText);
      await refreshCandidate();
      setResumeId(String(saved.id));
      setNotice("Resume saved to your candidate account.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save resume.");
    } finally {
      setLoading(false);
    }
  }

  async function onFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setError("");
    try {
      setResumeText(await extractResumeText(file));
      setNotice("Resume text extracted. Save it to attach it to your profile.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not read file.");
    }
  }

  async function onRunMatch() {
    if (!resumeId || !jobPostId) return;
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const result = await createMatch(user, Number(resumeId), Number(jobPostId));
      setCurrent(result);
      setMatches((items) => [result, ...items.filter((item) => item.id !== result.id)]);
      setNotice("Match created from your resume and selected job post.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create match.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <DashboardMetrics latest={current} itemCount={resumes.length} itemLabel="Saved resumes" matchCount={matches.length} mode="Candidate" />
      <section className="workspace role-workspace">
        <div className="panel input-panel">
          <PanelTitle title="Candidate profile" subtitle="Only this candidate session can edit this profile." />
          <label className="field">
            <span>Headline</span>
            <input value={profile.headline} onChange={(event) => setProfile({ ...profile, headline: event.target.value })} />
          </label>
          <label className="field">
            <span>Skills</span>
            <input value={profile.skills} onChange={(event) => setProfile({ ...profile, skills: event.target.value })} />
          </label>
          <label className="field">
            <span>Bio</span>
            <textarea value={profile.bio} onChange={(event) => setProfile({ ...profile, bio: event.target.value })} />
          </label>
          <button className="secondary-action" onClick={onSaveProfile}>Save profile</button>
        </div>

        <div className="panel input-panel">
          <PanelTitle title="My resume" subtitle="Upload or edit only your own resume." />
          <label className="field">
            <span>Existing resume</span>
            <select value={resumeId} onChange={(event) => {
              const selected = resumes.find((resume) => resume.id === Number(event.target.value));
              setResumeId(event.target.value);
              if (selected) {
                setResumeTitle(selected.title);
                setResumeText(selected.resume_text);
              }
            }}>
              <option value="">Create new resume</option>
              {resumes.map((resume) => <option key={resume.id} value={resume.id}>{resume.title}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Resume title</span>
            <input value={resumeTitle} onChange={(event) => setResumeTitle(event.target.value)} />
          </label>
          <label className="file-button inline-upload">
            Upload TXT/PDF
            <input type="file" accept=".txt,.pdf,text/plain,application/pdf" onChange={onFileChange} />
          </label>
          <label className="field">
            <span>Resume text</span>
            <textarea value={resumeText} onChange={(event) => setResumeText(event.target.value)} />
          </label>
          <button className="primary-action" disabled={loading || resumeText.trim().length < 20} onClick={onSaveResume}>
            {loading ? <span className="spinner" /> : null}
            Save resume
          </button>
        </div>

        <div className="panel result-panel">
          <PanelTitle title="Job matches" subtitle="Candidates can view public jobs and match only their own resume." />
          <label className="field">
            <span>Resume</span>
            <select value={resumeId} onChange={(event) => setResumeId(event.target.value)}>
              <option value="">Select resume</option>
              {resumes.map((resume) => <option key={resume.id} value={resume.id}>{resume.title}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Job post</span>
            <select value={jobPostId} onChange={(event) => setJobPostId(event.target.value)}>
              <option value="">Select job</option>
              {jobs.map((job) => <option key={job.id} value={job.id}>{job.title} · {job.company || "Unknown company"}</option>)}
            </select>
          </label>
          <button className="primary-action" disabled={loading || !resumeId || !jobPostId} onClick={onRunMatch}>
            {loading ? <span className="spinner" /> : null}
            Run match
          </button>
          <StatusMessages error={error} notice={notice} />
          <MatchResult result={current} />
        </div>
      </section>
      <MatchHistory matches={matches} setCurrent={setCurrent} />
    </>
  );
}

function RecruiterDashboard({ user }: { user: User }) {
  const [profile, setProfile] = useState<RecruiterProfile>({ id: 0, user_id: user.id, company: "", title: "" });
  const [jobs, setJobs] = useState<JobPost[]>([]);
  const [matches, setMatches] = useState<Analysis[]>([]);
  const [jobId, setJobId] = useState("");
  const [jobTitle, setJobTitle] = useState("Software Engineer");
  const [company, setCompany] = useState("Acme");
  const [description, setDescription] = useState(sampleJob);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    refreshRecruiter();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id]);

  async function refreshRecruiter() {
    setError("");
    try {
      const [nextProfile, nextJobs, nextMatches] = await Promise.all([getRecruiterProfile(user), listMyJobPosts(user), listMatches(user)]);
      setProfile(nextProfile);
      setJobs(nextJobs);
      setMatches(nextMatches);
      setJobId(nextJobs[0] ? String(nextJobs[0].id) : "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load recruiter workspace.");
    }
  }

  async function onSaveProfile() {
    setError("");
    setNotice("");
    const saved = await saveRecruiterProfile(user, { company: profile.company, title: profile.title });
    setProfile(saved);
    setNotice("Recruiter profile saved.");
  }

  async function onSaveJob() {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const jobInput: JobPostInput = {
        title: jobTitle,
        company,
        location: "",
        work_mode: "remote",
        salary_range: "",
        experience_level: "",
        required_skills: "",
        nice_to_have_skills: "",
        description,
      };
      const saved = jobId ? await updateJobPost(user, Number(jobId), jobInput) : await createJobPost(user, jobInput);
      await refreshRecruiter();
      setJobId(String(saved.id));
      setNotice("Job post saved to your recruiter account.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save job post.");
    } finally {
      setLoading(false);
    }
  }

  const latest = matches[0] ?? null;

  return (
    <>
      <DashboardMetrics latest={latest} itemCount={jobs.length} itemLabel="My job posts" matchCount={matches.length} mode="Recruiter" />
      <section className="workspace role-workspace">
        <div className="panel input-panel">
          <PanelTitle title="Recruiter profile" subtitle="Only this recruiter session can edit this profile." />
          <label className="field">
            <span>Company</span>
            <input value={profile.company} onChange={(event) => setProfile({ ...profile, company: event.target.value })} />
          </label>
          <label className="field">
            <span>Title</span>
            <input value={profile.title} onChange={(event) => setProfile({ ...profile, title: event.target.value })} />
          </label>
          <button className="secondary-action" onClick={onSaveProfile}>Save profile</button>
        </div>

        <div className="panel input-panel">
          <PanelTitle title="My job posts" subtitle="Create or edit only job posts owned by this recruiter." />
          <label className="field">
            <span>Existing job</span>
            <select value={jobId} onChange={(event) => {
              const selected = jobs.find((job) => job.id === Number(event.target.value));
              setJobId(event.target.value);
              if (selected) {
                setJobTitle(selected.title);
                setCompany(selected.company);
                setDescription(selected.description);
              }
            }}>
              <option value="">Create new job post</option>
              {jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}
            </select>
          </label>
          <label className="field">
            <span>Job title</span>
            <input value={jobTitle} onChange={(event) => setJobTitle(event.target.value)} />
          </label>
          <label className="field">
            <span>Company</span>
            <input value={company} onChange={(event) => setCompany(event.target.value)} />
          </label>
          <label className="field">
            <span>Description</span>
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <button className="primary-action" disabled={loading || description.trim().length < 20} onClick={onSaveJob}>
            {loading ? <span className="spinner" /> : null}
            Save job post
          </button>
          <StatusMessages error={error} notice={notice} />
        </div>

        <div className="panel result-panel">
          <PanelTitle title="Candidate match results" subtitle="Recruiters can view matches connected to their own job posts." />
          <MatchResult result={latest} />
        </div>
      </section>
      <MatchHistory matches={matches} setCurrent={() => undefined} />
    </>
  );
}

function DashboardMetrics({ latest, itemCount, itemLabel, matchCount, mode }: { latest: Analysis | null; itemCount: number; itemLabel: string; matchCount: number; mode: string }) {
  const average = useMemo(() => latest?.match_score ?? 0, [latest]);
  return (
    <section className="metrics-grid">
      <div className="metric">
        <span>Latest score</span>
        <strong>{latest ? latest.match_score : "--"}</strong>
        <small>{latest ? scoreLabel(latest.match_score) : "No match yet"}</small>
      </div>
      <div className="metric">
        <span>{itemLabel}</span>
        <strong>{itemCount}</strong>
        <small>Owned by this session</small>
      </div>
      <div className="metric">
        <span>Matches</span>
        <strong>{matchCount}</strong>
        <small>Role-filtered results</small>
      </div>
      <div className="metric">
        <span>Workspace</span>
        <strong>{mode}</strong>
        <small>{average ? `${average}/100 latest match` : "Access controlled"}</small>
      </div>
    </section>
  );
}

function PanelTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="panel-header">
      <div>
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>
    </div>
  );
}

function StatusMessages({ error, notice }: { error: string; notice: string }) {
  return (
    <>
      {error ? (
        <div className="error" role="alert">
          <strong>Action blocked</strong>
          <span>{error}</span>
        </div>
      ) : null}
      {notice ? <div className="notice">{notice}</div> : null}
    </>
  );
}

function MatchResult({ result }: { result: Analysis | null }) {
  if (!result) return <p className="empty">No match results yet.</p>;

  return (
    <div className="match-result">
      <div className="score-row">
        <div className={`score-number ${scoreTone(result.match_score)}`}>
          <span>{result.match_score}</span>
          <small>/100</small>
        </div>
        <div className="score-track">
          <div>
            <span style={{ width: `${result.match_score}%` }} />
          </div>
          <small>{scoreLabel(result.match_score)}</small>
        </div>
      </div>
      <p className="summary">{result.summary}</p>
      <div className="section-title">
        <h3>Skill gaps</h3>
        <span>{result.missing_skills.length} gaps</span>
      </div>
      <div className="skill-bars">
        {result.missing_skills.length ? (
          result.missing_skills.slice(0, 6).map((skill, index) => {
            const impact = Math.max(38, 92 - index * 8);
            return (
              <div className="skill-gap" key={skill}>
                <div>
                  <span>{skill}</span>
                  <strong>{impact}% priority</strong>
                </div>
                <div className="gap-track">
                  <span style={{ width: `${impact}%` }} />
                </div>
              </div>
            );
          })
        ) : (
          <div className="no-gap">No obvious missing skills found.</div>
        )}
      </div>
      <div className="section-title">
        <h3>Recommended improvements</h3>
        <span>{result.improvements.length} actions</span>
      </div>
      <ul className="improvements">
        {result.improvements.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}

function MatchHistory({ matches, setCurrent }: { matches: Analysis[]; setCurrent: (analysis: Analysis) => void }) {
  return (
    <section className="panel history-wide">
      <PanelTitle title="Match history" subtitle="Only results connected to the active session are returned by the backend." />
      <div className="history-list horizontal-history">
        {matches.length ? matches.map((item) => (
          <button key={item.id} className="history-item" onClick={() => setCurrent(item)}>
            <div>
              <span>{new Date(item.created_at).toLocaleString()}</span>
              <small>{scoreLabel(item.match_score)}</small>
            </div>
            <strong>{item.match_score}</strong>
          </button>
        )) : <p className="empty">No saved matches yet.</p>}
      </div>
    </section>
  );
}
