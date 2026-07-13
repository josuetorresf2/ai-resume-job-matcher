import fs from "node:fs";
import path from "node:path";
import puppeteer from "puppeteer-core";

const frontendUrl = process.env.FRONTEND_URL ?? "http://127.0.0.1:3000";
const backendUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
const chromeCandidates = [
  process.env.PUPPETEER_EXECUTABLE_PATH,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome",
  "/usr/bin/chromium",
  "/usr/bin/chromium-browser",
].filter(Boolean);
const executablePath = chromeCandidates.find((candidate) => fs.existsSync(candidate));
const artifactDir = path.join(process.cwd(), "e2e", "artifacts");

function uniqueEmail(prefix) {
  return `${prefix}.${Date.now()}@example.com`;
}

async function assertService(url, name) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${name} is not ready at ${url}. Received HTTP ${response.status}.`);
  }
}

async function waitForText(page, text, timeout = 10000) {
  await page.waitForFunction(
    (expected) => document.body.innerText.includes(expected),
    { timeout },
    text,
  );
}

async function clickTestId(page, testId) {
  await page.waitForSelector(`[data-testid="${testId}"]`, { visible: true });
  await page.click(`[data-testid="${testId}"]`);
}

async function waitForHydration(page) {
  await page.waitForFunction(
    () => {
      const loadedScripts = performance
        .getEntriesByType("resource")
        .map((entry) => entry.name);
      return loadedScripts.some((name) => name.includes("/_next/static/chunks/main-app.js"))
        && loadedScripts.some((name) => name.includes("/_next/static/chunks/app/page.js"));
    },
    { timeout: 12000 },
  );
  await page.waitForFunction(() => document.readyState === "complete", { timeout: 12000 });
  await new Promise((resolve) => setTimeout(resolve, 500));
}

async function fillTestId(page, testId, value) {
  const selector = `[data-testid="${testId}"]`;
  await page.waitForSelector(selector, { visible: true });
  await page.click(selector, { clickCount: 3 });
  await page.keyboard.press("Backspace");
  await page.type(selector, value);
}

async function login(page, role, channel = "email") {
  const label = role === "candidate" ? "Candidate" : "Recruiter";
  await page.goto(`${frontendUrl}?e2e=${role}-${Date.now()}`, { waitUntil: "domcontentloaded" });
  await waitForHydration(page);
  await clickTestId(page, `role-${role}`);
  await fillTestId(page, "auth-name", `E2E ${label}`);
  await fillTestId(page, "auth-email", uniqueEmail(role));
  await fillTestId(page, "auth-phone", "+593987654321");
  await fillTestId(page, "auth-password", "Password123!");
  await page.select('[data-testid="auth-verification-channel"]', channel);
  await clickTestId(page, "auth-continue");
  await waitForText(page, role === "candidate" ? "Candidate profile" : "Recruiter profile");
}

async function verifyDemoAccount(page) {
  await waitForText(page, "Account verification");
  await clickTestId(page, "request-verification-code");
  await waitForText(page, "Demo code: 123456");
  await clickTestId(page, "verify-code");
  await page.waitForFunction(() => !document.body.innerText.includes("Account verification"), { timeout: 10000 });
}

async function runCandidateFlow(page) {
  await login(page, "candidate", "whatsapp");
  await verifyDemoAccount(page);
  await fillTestId(
    page,
    "resume-text",
    "Backend engineer with Python, FastAPI, SQL, Docker, REST APIs, GitHub Actions, testing, and cloud deployment experience.",
  );
  await clickTestId(page, "save-resume");
  await waitForText(page, "Resume saved to your candidate account.");
  await clickTestId(page, "practice-interview");
  await waitForText(page, "Practice interview generated.");
  await waitForText(page, "Interview Score");
}

async function runRecruiterFlow(page) {
  await login(page, "recruiter");
  await fillTestId(page, "job-title", "E2E Backend Automation Engineer");
  await fillTestId(page, "job-company", "FairHire Test Labs");
  await fillTestId(page, "job-location", "Quito, Ecuador");
  await fillTestId(page, "job-salary", "$1800-$3000");
  await fillTestId(page, "job-experience", "Mid");
  await fillTestId(page, "job-required-skills", "Python, TypeScript, REST APIs, Docker, CI/CD");
  await fillTestId(page, "job-nice-skills", "Temporal, Puppeteer, AWS");
  await fillTestId(
    page,
    "job-description",
    "Build reliable automation workflows, integrate REST APIs, write tests, improve observability, and support small businesses hiring verified technical talent.",
  );
  await clickTestId(page, "save-job");
  await waitForText(page, "Job post saved to your recruiter account.");
}

async function main() {
  if (!executablePath) {
    throw new Error("Chrome or Chromium was not found. Set PUPPETEER_EXECUTABLE_PATH to run E2E tests.");
  }

  await assertService(`${backendUrl}/health`, "Backend");
  await assertService(frontendUrl, "Frontend");

  const browser = await puppeteer.launch({
    executablePath,
    headless: "new",
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
  });

  try {
    const page = await browser.newPage();
    page.setDefaultTimeout(12000);
    await page.setViewport({ width: 1366, height: 900 });
    await runCandidateFlow(page);
    await runRecruiterFlow(page);
    console.log("FairHire E2E passed: candidate resume/interview flow and recruiter job draft flow.");
  } catch (error) {
    fs.mkdirSync(artifactDir, { recursive: true });
    const pages = await browser.pages();
    const activePage = pages[pages.length - 1];
    if (activePage) {
      await activePage.screenshot({ path: path.join(artifactDir, "failure.png"), fullPage: true });
    }
    throw error;
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
