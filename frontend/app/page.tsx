"use client";

import { useEffect, useMemo, useState } from "react";
import { Analysis, createAnalysis, extractResumeText, listAnalyses } from "../lib/api";
import { scoreLabel, scoreTone } from "../lib/score";

const sampleResume =
  "Full-stack developer with Python, FastAPI, React, SQL, Docker, Git, and REST API experience. Built dashboards and automated workflows for internal teams.";
const sampleJob =
  "Hiring a software engineer with Python, FastAPI, React, Docker, SQL, AWS, GitHub Actions, and experience building production REST APIs.";

export default function Home() {
  const [resumeText, setResumeText] = useState(sampleResume);
  const [jobDescription, setJobDescription] = useState(sampleJob);
  const [history, setHistory] = useState<Analysis[]>([]);
  const [current, setCurrent] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listAnalyses().then(setHistory).catch(() => setHistory([]));
  }, []);

  const averageScore = useMemo(() => {
    if (history.length === 0) return 0;
    return Math.round(history.reduce((sum, item) => sum + item.match_score, 0) / history.length);
  }, [history]);

  async function onAnalyze() {
    setError("");
    setLoading(true);
    try {
      const result = await createAnalysis(resumeText, jobDescription);
      setCurrent(result);
      setHistory((items) => [result, ...items.filter((item) => item.id !== result.id)]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not read file.");
    }
  }

  const result = current ?? history[0] ?? null;

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Portfolio Project 1</p>
          <h1>AI Resume & Job Matcher</h1>
        </div>
        <div className="status-pill">FastAPI + Next.js + SQLite + OpenAI</div>
      </header>

      <section className="metrics-grid">
        <div className="metric">
          <span>Latest score</span>
          <strong>{result ? result.match_score : 0}</strong>
        </div>
        <div className="metric">
          <span>Saved analyses</span>
          <strong>{history.length}</strong>
        </div>
        <div className="metric">
          <span>Average score</span>
          <strong>{averageScore}</strong>
        </div>
        <div className="metric">
          <span>Mode</span>
          <strong>{result?.source ?? "ready"}</strong>
        </div>
      </section>

      <section className="workspace">
        <div className="panel input-panel">
          <div className="panel-header">
            <h2>Inputs</h2>
            <label className="file-button">
              Upload resume
              <input type="file" accept=".txt,.pdf,text/plain,application/pdf" onChange={onFileChange} />
            </label>
          </div>

          <label className="field">
            <span>Resume text</span>
            <textarea value={resumeText} onChange={(event) => setResumeText(event.target.value)} />
          </label>

          <label className="field">
            <span>Job description</span>
            <textarea value={jobDescription} onChange={(event) => setJobDescription(event.target.value)} />
          </label>

          {error ? <p className="error">{error}</p> : null}
          <button className="primary-action" disabled={loading} onClick={onAnalyze}>
            {loading ? "Analyzing..." : "Analyze match"}
          </button>
        </div>

        <div className="panel result-panel">
          <div className="panel-header">
            <h2>Match Results</h2>
            {result ? <span className={`score-badge ${scoreTone(result.match_score)}`}>{scoreLabel(result.match_score)}</span> : null}
          </div>

          {result ? (
            <>
              <div className="score-row">
                <div className="score-number">{result.match_score}</div>
                <div className="score-track">
                  <div style={{ width: `${result.match_score}%` }} />
                </div>
              </div>
              <p className="summary">{result.summary}</p>

              <h3>Missing skills</h3>
              <div className="chips">
                {result.missing_skills.length ? result.missing_skills.map((skill) => <span key={skill}>{skill}</span>) : <span>No obvious gaps</span>}
              </div>

              <h3>Resume improvements</h3>
              <ul className="improvements">
                {result.improvements.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          ) : (
            <p className="empty">Run an analysis to see match quality, gaps, and suggested edits.</p>
          )}
        </div>

        <aside className="panel history-panel">
          <div className="panel-header">
            <h2>Previous Analyses</h2>
          </div>
          <div className="history-list">
            {history.length ? (
              history.map((item) => (
                <button key={item.id} className="history-item" onClick={() => setCurrent(item)}>
                  <span>{new Date(item.created_at).toLocaleString()}</span>
                  <strong>{item.match_score}</strong>
                </button>
              ))
            ) : (
              <p className="empty">No saved analyses yet.</p>
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}
