"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Analysis,
  CandidateProfile,
  CandidateMetrics,
  CareerCoachPlan,
  GitHubAnalysis,
  InterviewPractice,
  JobDashboardItem,
  JobPostInput,
  JobPost,
  RankedCandidateMatch,
  RecruiterProfile,
  RecruiterMetrics,
  Resume,
  Role,
  User,
  createJobPost,
  createMatch,
  createResume,
  deleteJobPost,
  extractResumeText,
  analyzeGitHub,
  getCandidateProfile,
  getCandidateMetrics,
  getCareerCoachPlan,
  getRecruiterProfile,
  getRecruiterDashboard,
  getRecruiterMetrics,
  getSalaryIntelligence,
  listRankedCandidates,
  listJobPosts,
  listAdminCompanies,
  listAdminFlaggedJobs,
  listMatches,
  listMyJobPosts,
  listResumes,
  mockLogin,
  publishJobPost,
  reportJobPost,
  removeAdminJob,
  reviewAdminCompany,
  saveCandidateProfile,
  saveRecruiterProfile,
  updateMatchReview,
  updateJobPost,
  updatePreferences,
  updateResume,
  verifyAccount,
  practiceInterview,
  SalaryIntelligence,
} from "../lib/api";
import { scoreLabel, scoreTone } from "../lib/score";

const sampleResume =
  "Full-stack developer with Python, FastAPI, React, SQL, Docker, Git, and REST API experience. Built dashboards and automated workflows for internal teams.";
const sampleJob =
  "Hiring a software engineer with Python, FastAPI, React, Docker, SQL, AWS, GitHub Actions, and experience building production REST APIs.";

type SupportedLanguage = "en" | "es" | "pt" | "fr" | "sw";
type TargetMarket = "latin-america" | "africa" | "global-remote";

const LANGUAGE_OPTIONS: Array<{ value: SupportedLanguage; label: string }> = [
  { value: "en", label: "English" },
  { value: "es", label: "Espanol" },
  { value: "pt", label: "Portugues" },
  { value: "fr", label: "Francais" },
  { value: "sw", label: "Kiswahili" },
];

const MARKET_OPTIONS: Array<{ value: TargetMarket; labelKey: "marketLatam" | "marketAfrica" | "marketGlobal" }> = [
  { value: "latin-america", labelKey: "marketLatam" },
  { value: "africa", labelKey: "marketAfrica" },
  { value: "global-remote", labelKey: "marketGlobal" },
];

const MARKET_JOBS: Record<TargetMarket, Array<{ role: string; tags: string[]; demand: number; signal: string }>> = {
  "latin-america": [
    { role: "Remote Python Backend Developer", tags: ["python", "backend", "fastapi", "api"], demand: 86, signal: "Remote LATAM contractor demand is strong." },
    { role: "React Frontend Developer", tags: ["react", "frontend", "javascript", "typescript"], demand: 82, signal: "Small companies need portfolio-ready UI builders." },
    { role: "Bilingual Customer Support", tags: ["support", "customer", "english", "spanish"], demand: 74, signal: "English plus Spanish is a practical advantage." },
    { role: "Sales Development Representative", tags: ["sales", "crm", "sdr", "english"], demand: 71, signal: "Remote sales roles often hire across LATAM." },
  ],
  africa: [
    { role: "Mobile Money Support Specialist", tags: ["support", "fintech", "mobile money", "customer"], demand: 84, signal: "Fintech and mobile money teams need verified talent." },
    { role: "Junior Data Analyst", tags: ["data", "excel", "sql", "analytics"], demand: 79, signal: "Data roles are growing across local and remote teams." },
    { role: "Python Automation Developer", tags: ["python", "automation", "backend", "api"], demand: 76, signal: "Automation helps small companies operate with lean teams." },
    { role: "Community Operations Associate", tags: ["operations", "community", "support", "trust"], demand: 73, signal: "Trust, safety, and marketplace ops are a strong fit." },
  ],
  "global-remote": [
    { role: "Full-stack Software Engineer", tags: ["software", "react", "python", "full-stack"], demand: 88, signal: "Remote teams reward proof of shipping complete products." },
    { role: "AI Workflow Specialist", tags: ["ai", "automation", "operations", "prompt"], demand: 81, signal: "Small companies need AI workflows without enterprise tools." },
    { role: "Technical Virtual Assistant", tags: ["support", "operations", "documentation", "admin"], demand: 72, signal: "Documentation and reliable communication matter." },
    { role: "Product Designer", tags: ["design", "figma", "ui", "ux"], demand: 69, signal: "Lean startups look for practical product design portfolios." },
  ],
};

const COPY = {
  en: {
    eyebrow: "Free AI recruiting platform",
    title: "FairHire",
    subtitle: "Accessible recruiting workflows for candidates, recruiters, and small companies in underserved markets.",
    lightMode: "Light mode",
    darkMode: "Dark mode",
    lowBandwidth: "Low bandwidth",
    standardMode: "Standard mode",
    switchRole: "Switch role",
    authStatus: "Mock session auth",
    chooseWorkspace: "Choose your workspace",
    loginHelp: "Create an account with a role, password, language, and verification channel.",
    name: "Name",
    email: "Email",
    phoneNumber: "Phone number",
    phoneHint: "+593987654321",
    password: "Password",
    passwordHint: "At least 8 characters",
    language: "Language",
    verifyBy: "Verify by",
    recruiterRole: "I am a Recruiter",
    candidateRole: "I am a Candidate",
    adminRole: "Admin review",
    adminPerms: "Review company verification and remove flagged jobs.",
    continueAs: "Continue as",
    selectedRole: "selected role",
    formHint: "Select a role and create an account. Verification is a portfolio placeholder for email, SMS, or WhatsApp.",
    permissionModel: "Permission model",
    can: "Can",
    cannot: "Cannot",
    candidate: "Candidate",
    recruiter: "Recruiter",
    candidatePerms: "Can edit their own profile and resumes, run matches, practice interviews, and view career intelligence.",
    recruiterPerms: "Can edit their own profile and job posts, view match results tied to their jobs, and cannot modify candidate resumes.",
    candidateLanding: "Build your profile, upload a resume, and find roles that fit your skills.",
    recruiterLanding: "Post jobs, review ranked matches, and shortlist candidates with confidence.",
    candidateCannot: "Cannot edit recruiter job posts, company profiles, or private recruiter notes.",
    recruiterCannot: "Cannot edit candidate resumes, profiles, contact details, or personal data.",
    marketPreviewTitle: "Explore jobs before signing up",
    marketPreviewHelp: "Search by role and region to see where FairHire can help candidates and small companies first.",
    searchJobs: "What kind of job are you looking for?",
    jobSearchPlaceholder: "React, Python, customer support, sales...",
    targetMarket: "Target market",
    marketSignals: "Market signals",
    popularSearches: "Popular searches",
    openRoles: "available role types",
    remoteFriendly: "remote-friendly",
    salarySignal: "salary transparency",
    localHiring: "local hiring",
    noMarketMatch: "No exact preview yet. Try software, support, data, sales, or design.",
    marketLatam: "Latin America",
    marketAfrica: "Africa",
    marketGlobal: "Global remote",
    sessionIssue: "Session issue",
    enterName: "Enter your name before continuing.",
    enterEmail: "Enter a valid email before continuing.",
    enterPassword: "Use a password with at least 8 characters.",
    candidateProfile: "Candidate profile",
    candidateProfileHelp: "Only this candidate session can edit this profile.",
    headline: "Headline",
    skills: "Skills",
    bio: "Bio",
    proofOfWork: "Proof of work",
    proofOfWorkHelp: "Add links that prove what you can build: live demos, GitHub repos, portfolio, or technical writeups.",
    portfolioUrl: "Portfolio URL",
    githubProfile: "GitHub profile",
    linkedinProfile: "LinkedIn profile",
    projectDemos: "Project demo URLs",
    projectDemosHint: "One URL per line: live app, repo, case study, video demo, or documentation.",
    openPortfolio: "Open portfolio",
    openGitHub: "Open GitHub",
    openLinkedIn: "Open LinkedIn",
    openDemo: "Open demo",
    visibility: "Visibility",
    private: "Private",
    verifiedRecruiters: "Verified recruiters",
    public: "Public",
    saveProfile: "Save profile",
    resumeTitle: "Resume title",
    myResume: "My resume",
    myResumeHelp: "Upload or edit only your own resume.",
    existingResume: "Existing resume",
    createResume: "Create new resume",
    createJob: "Create new job post",
    uploadResume: "Upload TXT/PDF",
    resumeText: "Resume text",
    saveResume: "Save resume",
    jobMatches: "Job matches",
    jobMatchesHelp: "Candidates can view public jobs and match only their own resume.",
    resume: "Resume",
    jobPost: "Job post",
    selectResume: "Select resume",
    selectJob: "Select job",
    runMatch: "Run match",
    reportJob: "Report suspicious job",
    aiTools: "AI career tools",
    aiToolsHelp: "Practice interviews, create a growth roadmap, estimate salary ranges, and score your GitHub portfolio.",
    practiceInterview: "Practice Interview",
    careerCoach: "AI Career Coach",
    salaryIntel: "Salary Intelligence",
    githubAnalysis: "GitHub Analysis",
    githubUrl: "GitHub URL",
    portfolioScore: "Portfolio Score",
    interviewScore: "Interview Score",
    strengths: "Strengths",
    needsImprovement: "Needs Improvement",
    learn: "Learn",
    estimatedEffort: "Estimated effort",
    roadmap: "Roadmap",
    salaryRanges: "Salary ranges",
    recommendations: "Recommendations",
    actionBlocked: "Action blocked",
    latestScore: "Latest score",
    noMatchYet: "No match yet",
    savedResumes: "Saved resumes",
    myJobPosts: "My job posts",
    adminDashboard: "Admin review",
    companiesForReview: "Companies for review",
    flaggedJobs: "Flagged jobs",
    approve: "Approve",
    reject: "Reject",
    removeJob: "Remove job",
    noCompanies: "No companies to review.",
    noFlaggedJobs: "No flagged jobs.",
    applications: "Applications",
    averageMatch: "Average match",
    profileStrength: "Profile strength",
    candidatesApplied: "Candidates applied",
    interviewsScheduled: "Interviews scheduled",
    ownedBySession: "Owned by this session",
    matches: "Matches",
    roleFiltered: "Role-filtered results",
    workspace: "Workspace",
    accessControlled: "Access controlled",
    noResults: "No match results yet.",
    skillGaps: "Skill gaps",
    gaps: "gaps",
    noGaps: "No obvious missing skills found.",
    improvements: "Recommended improvements",
    actions: "actions",
    history: "Match history",
    historyHelp: "Only results connected to the active session are returned by the backend.",
    recruiterProfile: "Recruiter profile",
    recruiterProfileHelp: "Only this recruiter session can edit this profile.",
    company: "Company",
    location: "Location",
    workMode: "Work mode",
    remote: "Remote",
    hybrid: "Hybrid",
    onsite: "Onsite",
    salaryRange: "Salary range",
    experienceLevel: "Experience level",
    requiredSkills: "Required skills",
    niceToHaveSkills: "Nice-to-have skills",
    website: "Website",
    contactEmail: "Contact email",
    country: "Country",
    city: "City",
    companyDescription: "Company description",
    verifyAccount: "Verify account placeholder",
    saveJob: "Save job post",
    publishJob: "Publish job",
    candidateResults: "Candidate match results",
    candidateResultsHelp: "Recruiters can view matches connected to their own job posts.",
    status: "Status",
    quality: "Quality",
    spam: "Spam",
    trust: "Trust",
    unknownCompany: "Unknown company",
  },
  es: {
    eyebrow: "Plataforma gratuita de reclutamiento con IA",
    title: "FairHire",
    subtitle: "Flujos de reclutamiento accesibles para candidatos, reclutadores y pequenas empresas en mercados desatendidos.",
    lightMode: "Modo claro",
    darkMode: "Modo oscuro",
    lowBandwidth: "Bajo consumo",
    standardMode: "Modo normal",
    switchRole: "Cambiar rol",
    authStatus: "Sesion mock",
    chooseWorkspace: "Elige tu espacio",
    loginHelp: "Crea una cuenta con rol, password, idioma y canal de verificacion.",
    name: "Nombre",
    email: "Email",
    phoneNumber: "Telefono",
    phoneHint: "+593987654321",
    password: "Password",
    passwordHint: "Minimo 8 caracteres",
    language: "Idioma",
    verifyBy: "Verificar por",
    recruiterRole: "Soy reclutador",
    candidateRole: "Soy candidato",
    adminRole: "Revision admin",
    adminPerms: "Revisar verificacion de empresas y remover empleos reportados.",
    continueAs: "Continuar como",
    selectedRole: "rol seleccionado",
    formHint: "Selecciona un rol y crea una cuenta. La verificacion es un placeholder para email, SMS o WhatsApp.",
    permissionModel: "Modelo de permisos",
    can: "Puede",
    cannot: "No puede",
    candidate: "Candidato",
    recruiter: "Reclutador",
    candidatePerms: "Puede editar su perfil y resumes, correr matches, practicar entrevistas y ver inteligencia de carrera.",
    recruiterPerms: "Puede editar su perfil y empleos, ver matches de sus empleos y no puede modificar resumes de candidatos.",
    candidateLanding: "Crea tu perfil, sube tu resume y encuentra roles que calzan con tus habilidades.",
    recruiterLanding: "Publica empleos, revisa matches rankeados y guarda candidatos con confianza.",
    candidateCannot: "No puede editar empleos, perfiles de empresa ni notas privadas del reclutador.",
    recruiterCannot: "No puede editar resumes, perfiles, datos de contacto ni informacion personal de candidatos.",
    marketPreviewTitle: "Explora empleos antes de registrarte",
    marketPreviewHelp: "Busca por rol y region para ver donde FairHire puede ayudar primero a candidatos y pequenas empresas.",
    searchJobs: "Que tipo de empleo buscas?",
    jobSearchPlaceholder: "React, Python, soporte, ventas...",
    targetMarket: "Mercado objetivo",
    marketSignals: "Senales del mercado",
    popularSearches: "Busquedas populares",
    openRoles: "tipos de roles disponibles",
    remoteFriendly: "apto para remoto",
    salarySignal: "transparencia salarial",
    localHiring: "contratacion local",
    noMarketMatch: "No hay preview exacto todavia. Prueba software, soporte, data, ventas o diseno.",
    marketLatam: "Latinoamerica",
    marketAfrica: "Africa",
    marketGlobal: "Remoto global",
    sessionIssue: "Problema de sesion",
    enterName: "Ingresa tu nombre antes de continuar.",
    enterEmail: "Ingresa un email valido antes de continuar.",
    enterPassword: "Usa un password de al menos 8 caracteres.",
    candidateProfile: "Perfil del candidato",
    candidateProfileHelp: "Solo esta sesion de candidato puede editar este perfil.",
    headline: "Titulo profesional",
    skills: "Habilidades",
    bio: "Bio",
    proofOfWork: "Pruebas de trabajo",
    proofOfWorkHelp: "Agrega links que demuestren lo que puedes construir: demos, repos, portafolio o documentacion tecnica.",
    portfolioUrl: "URL del portafolio",
    githubProfile: "Perfil de GitHub",
    linkedinProfile: "Perfil de LinkedIn",
    projectDemos: "URLs de demos de proyectos",
    projectDemosHint: "Una URL por linea: app en vivo, repo, caso de estudio, video demo o documentacion.",
    openPortfolio: "Abrir portafolio",
    openGitHub: "Abrir GitHub",
    openLinkedIn: "Abrir LinkedIn",
    openDemo: "Abrir demo",
    visibility: "Visibilidad",
    private: "Privado",
    verifiedRecruiters: "Reclutadores verificados",
    public: "Publico",
    saveProfile: "Guardar perfil",
    resumeTitle: "Titulo del resume",
    myResume: "Mi resume",
    myResumeHelp: "Sube o edita solo tu propio resume.",
    existingResume: "Resume existente",
    createResume: "Crear nuevo resume",
    createJob: "Crear nuevo empleo",
    uploadResume: "Subir TXT/PDF",
    resumeText: "Texto del resume",
    saveResume: "Guardar resume",
    jobMatches: "Matches de empleo",
    jobMatchesHelp: "Los candidatos pueden ver empleos publicos y hacer match solo con su propio resume.",
    resume: "Resume",
    jobPost: "Empleo",
    selectResume: "Selecciona resume",
    selectJob: "Selecciona empleo",
    runMatch: "Correr match",
    reportJob: "Reportar empleo sospechoso",
    aiTools: "Herramientas de carrera con IA",
    aiToolsHelp: "Practica entrevistas, crea un roadmap, estima salarios y califica tu portafolio de GitHub.",
    practiceInterview: "Practicar entrevista",
    careerCoach: "Coach de carrera con IA",
    salaryIntel: "Inteligencia salarial",
    githubAnalysis: "Analisis de GitHub",
    githubUrl: "URL de GitHub",
    portfolioScore: "Score de portafolio",
    interviewScore: "Score de entrevista",
    strengths: "Fortalezas",
    needsImprovement: "Debe mejorar",
    learn: "Aprender",
    estimatedEffort: "Esfuerzo estimado",
    roadmap: "Roadmap",
    salaryRanges: "Rangos salariales",
    recommendations: "Recomendaciones",
    actionBlocked: "Accion bloqueada",
    latestScore: "Score reciente",
    noMatchYet: "Sin match todavia",
    savedResumes: "Resumes guardados",
    myJobPosts: "Mis empleos",
    adminDashboard: "Revision admin",
    companiesForReview: "Empresas para revisar",
    flaggedJobs: "Empleos reportados",
    approve: "Aprobar",
    reject: "Rechazar",
    removeJob: "Remover empleo",
    noCompanies: "No hay empresas para revisar.",
    noFlaggedJobs: "No hay empleos reportados.",
    applications: "Aplicaciones",
    averageMatch: "Match promedio",
    profileStrength: "Fuerza del perfil",
    candidatesApplied: "Candidatos aplicados",
    interviewsScheduled: "Entrevistas agendadas",
    ownedBySession: "Propiedad de esta sesion",
    matches: "Matches",
    roleFiltered: "Resultados filtrados por rol",
    workspace: "Espacio",
    accessControlled: "Acceso controlado",
    noResults: "No hay resultados todavia.",
    skillGaps: "Brechas de habilidades",
    gaps: "brechas",
    noGaps: "No se encontraron brechas claras.",
    improvements: "Mejoras recomendadas",
    actions: "acciones",
    history: "Historial de matches",
    historyHelp: "El backend solo devuelve resultados conectados a la sesion activa.",
    recruiterProfile: "Perfil del reclutador",
    recruiterProfileHelp: "Solo esta sesion de reclutador puede editar este perfil.",
    company: "Empresa",
    location: "Ubicacion",
    workMode: "Modalidad",
    remote: "Remoto",
    hybrid: "Hibrido",
    onsite: "Presencial",
    salaryRange: "Rango salarial",
    experienceLevel: "Nivel de experiencia",
    requiredSkills: "Habilidades requeridas",
    niceToHaveSkills: "Habilidades deseadas",
    website: "Website",
    contactEmail: "Email de contacto",
    country: "Pais",
    city: "Ciudad",
    companyDescription: "Descripcion de empresa",
    verifyAccount: "Verificar cuenta placeholder",
    saveJob: "Guardar empleo",
    publishJob: "Publicar empleo",
    candidateResults: "Resultados de candidatos",
    candidateResultsHelp: "Los reclutadores pueden ver matches conectados a sus empleos.",
    status: "Estado",
    quality: "Calidad",
    spam: "Spam",
    trust: "Confianza",
    unknownCompany: "Empresa desconocida",
  },
};

const LOCALIZED_COPY = {
  ...COPY,
  pt: {
    ...COPY.en,
    eyebrow: "Plataforma gratuita de recrutamento com IA",
    subtitle: "Fluxos de recrutamento acessiveis para candidatos, recrutadores e pequenas empresas em mercados desatendidos.",
    chooseWorkspace: "Escolha seu espaco",
    loginHelp: "Crie uma conta com funcao, senha, idioma e canal de verificacao.",
    recruiterRole: "Sou recrutador",
    candidateRole: "Sou candidato",
    continueAs: "Continuar como",
    selectedRole: "funcao selecionada",
    formHint: "Escolha primeiro seu perfil. Depois voce informa seus dados para criar a conta.",
    marketPreviewTitle: "Explore vagas antes de se cadastrar",
    marketPreviewHelp: "Pesquise por cargo e regiao para ver onde a FairHire pode ajudar candidatos e pequenas empresas.",
    searchJobs: "Que tipo de vaga voce procura?",
    targetMarket: "Mercado alvo",
    marketSignals: "Sinais do mercado",
    popularSearches: "Buscas populares",
    marketLatam: "America Latina",
    marketAfrica: "Africa",
    marketGlobal: "Remoto global",
  },
  fr: {
    ...COPY.en,
    eyebrow: "Plateforme gratuite de recrutement avec IA",
    subtitle: "Des parcours de recrutement accessibles pour les candidats, recruteurs et petites entreprises dans les marches mal desservis.",
    chooseWorkspace: "Choisissez votre espace",
    loginHelp: "Creez un compte avec role, mot de passe, langue et canal de verification.",
    recruiterRole: "Je suis recruteur",
    candidateRole: "Je suis candidat",
    continueAs: "Continuer comme",
    selectedRole: "role selectionne",
    formHint: "Choisissez d'abord votre profil. Ensuite, ajoutez vos informations pour creer le compte.",
    marketPreviewTitle: "Explorez des emplois avant l'inscription",
    marketPreviewHelp: "Recherchez par role et region pour voir ou FairHire peut aider les candidats et petites entreprises.",
    searchJobs: "Quel type d'emploi cherchez-vous?",
    targetMarket: "Marche cible",
    marketSignals: "Signaux du marche",
    popularSearches: "Recherches populaires",
    marketLatam: "Amerique latine",
    marketAfrica: "Afrique",
    marketGlobal: "Remote global",
  },
  sw: {
    ...COPY.en,
    eyebrow: "Jukwaa la bure la ajira kwa AI",
    subtitle: "Njia rahisi za ajira kwa wagombea, waajiri, na kampuni ndogo katika masoko yasiyohudumiwa vya kutosha.",
    chooseWorkspace: "Chagua nafasi yako",
    loginHelp: "Fungua akaunti kwa jukumu, nenosiri, lugha, na njia ya uthibitisho.",
    recruiterRole: "Mimi ni mwajiri",
    candidateRole: "Mimi ni mgombea",
    continueAs: "Endelea kama",
    selectedRole: "jukumu lililochaguliwa",
    formHint: "Chagua kwanza jukumu lako. Kisha ongeza taarifa zako kuunda akaunti.",
    marketPreviewTitle: "Angalia kazi kabla ya kujisajili",
    marketPreviewHelp: "Tafuta kwa aina ya kazi na eneo ili kuona FairHire inaweza kusaidia wapi kwanza.",
    searchJobs: "Unatafuta kazi ya aina gani?",
    targetMarket: "Soko lengwa",
    marketSignals: "Viashiria vya soko",
    popularSearches: "Utafutaji maarufu",
    marketLatam: "Amerika ya Kusini",
    marketAfrica: "Afrika",
    marketGlobal: "Remote duniani",
  },
};

type Copy = typeof COPY.en;

export default function Home() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [role, setRole] = useState<Role | null>(null);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [language, setLanguage] = useState<SupportedLanguage>("en");
  const [verificationChannel, setVerificationChannel] = useState<"email" | "sms" | "whatsapp">("email");
  const [jobSearch, setJobSearch] = useState("");
  const [targetMarket, setTargetMarket] = useState<TargetMarket>("latin-america");
  const [adminMode, setAdminMode] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const c = LOCALIZED_COPY[user?.language ?? language];

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    setAdminMode(new URLSearchParams(window.location.search).get("admin") === "1");
  }, []);

  async function onLogin(selectedRole: Role) {
    setError("");
    if (!name.trim()) {
      setError(c.enterName);
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      setError(c.enterEmail);
      return;
    }
    if (password.length < 8) {
      setError(c.enterPassword);
      return;
    }
    setLoading(true);
    try {
      const session = await mockLogin(name.trim(), email.trim(), phoneNumber.trim(), password, selectedRole, language, verificationChannel);
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
    setSelectedRole(null);
    setError("");
  }

  async function changeLanguage(nextLanguage: SupportedLanguage) {
    setLanguage(nextLanguage);
    if (!user) return;
    try {
      const updated = await updatePreferences(user, nextLanguage, user.low_bandwidth);
      setUser(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update language.");
    }
  }

  async function toggleLowBandwidth() {
    if (!user) return;
    try {
      const updated = await updatePreferences(user, user.language, user.low_bandwidth ? 0 : 1);
      setUser(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update low-bandwidth mode.");
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">{c.eyebrow}</p>
          <h1>{c.title}</h1>
          <p className="subtitle">{c.subtitle}</p>
        </div>
        <div className="topbar-actions">
          <select className="compact-select" value={user?.language ?? language} onChange={(event) => changeLanguage(event.target.value as SupportedLanguage)}>
            {LANGUAGE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <button className="theme-toggle" onClick={() => setTheme((value) => (value === "dark" ? "light" : "dark"))}>
            {theme === "dark" ? c.lightMode : c.darkMode}
          </button>
          {user ? (
            <button className="theme-toggle" onClick={toggleLowBandwidth}>
              {user.low_bandwidth ? c.standardMode : c.lowBandwidth}
            </button>
          ) : null}
          {user ? <button className="theme-toggle" onClick={resetSession}>{c.switchRole}</button> : null}
          <div className="status-pill">{user ? `${user.name} - ${user.role}` : c.authStatus}</div>
        </div>
      </header>

      {!user || !role ? (
        <RoleSelection
          name={name}
          email={email}
          phoneNumber={phoneNumber}
          password={password}
          language={language}
          verificationChannel={verificationChannel}
          jobSearch={jobSearch}
          targetMarket={targetMarket}
          c={c}
          error={error}
          loading={loading}
          selectedRole={selectedRole}
          setName={setName}
          setEmail={setEmail}
          setPhoneNumber={setPhoneNumber}
          setPassword={setPassword}
          setLanguage={setLanguage}
          setVerificationChannel={setVerificationChannel}
          setJobSearch={setJobSearch}
          setTargetMarket={setTargetMarket}
          setSelectedRole={setSelectedRole}
          onLogin={onLogin}
          adminMode={adminMode}
        />
      ) : role === "candidate" ? (
        <CandidateDashboard user={user} c={c} />
      ) : role === "recruiter" ? (
        <RecruiterDashboard user={user} c={c} />
      ) : (
        <AdminDashboard user={user} c={c} />
      )}
    </main>
  );
}

function RoleSelection({
  name,
  email,
  phoneNumber,
  password,
  language,
  verificationChannel,
  jobSearch,
  targetMarket,
  c,
  error,
  loading,
  selectedRole,
  setName,
  setEmail,
  setPhoneNumber,
  setPassword,
  setLanguage,
  setVerificationChannel,
  setJobSearch,
  setTargetMarket,
  setSelectedRole,
  onLogin,
  adminMode,
}: {
  name: string;
  email: string;
  phoneNumber: string;
  password: string;
  language: SupportedLanguage;
  verificationChannel: "email" | "sms" | "whatsapp";
  jobSearch: string;
  targetMarket: TargetMarket;
  c: Copy;
  error: string;
  loading: boolean;
  selectedRole: Role | null;
  setName: (value: string) => void;
  setEmail: (value: string) => void;
  setPhoneNumber: (value: string) => void;
  setPassword: (value: string) => void;
  setLanguage: (value: SupportedLanguage) => void;
  setVerificationChannel: (value: "email" | "sms" | "whatsapp") => void;
  setJobSearch: (value: string) => void;
  setTargetMarket: (value: TargetMarket) => void;
  setSelectedRole: (value: Role | null) => void;
  onLogin: (role: Role) => Promise<void>;
  adminMode: boolean;
}) {
  const canLogin = Boolean(selectedRole) && !loading;
  const selectedRoleLabel = selectedRole === "candidate" ? c.candidate : selectedRole === "admin" ? c.adminRole : c.recruiter;
  const normalizedSearch = jobSearch.trim().toLowerCase();
  const marketJobs = MARKET_JOBS[targetMarket];
  const previewJobs = normalizedSearch
    ? marketJobs.filter((job) => [job.role, ...job.tags].join(" ").toLowerCase().includes(normalizedSearch))
    : marketJobs;
  const visiblePreviewJobs = previewJobs.slice(0, 3);

  return (
    <section className={selectedRole ? "role-grid role-grid-form" : "role-grid"}>
      <div className={selectedRole ? "panel role-panel" : "panel role-panel role-panel-intro"}>
        <div className="panel-header">
          <div>
            <h2>{c.chooseWorkspace}</h2>
            <p>{selectedRole ? c.loginHelp : c.formHint}</p>
          </div>
        </div>
        {!selectedRole ? (
          <div className="role-picker role-picker-intro" aria-label={c.chooseWorkspace}>
            <button className="role-choice" data-testid="role-recruiter" disabled={loading} onClick={() => setSelectedRole("recruiter")}>
              <span>{c.recruiterRole}</span>
              <small>{c.recruiterLanding}</small>
            </button>
            <button className="role-choice" data-testid="role-candidate" disabled={loading} onClick={() => setSelectedRole("candidate")}>
              <span>{c.candidateRole}</span>
              <small>{c.candidateLanding}</small>
            </button>
            {adminMode ? (
              <button className="secondary-action compact-action" disabled={loading} onClick={() => setSelectedRole("admin")}>
                {c.adminRole}
              </button>
            ) : null}
          </div>
        ) : (
          <>
            <div className="selected-role-summary">
              <div>
                <span>{c.selectedRole}</span>
                <strong>{selectedRoleLabel}</strong>
              </div>
              <button className="secondary-action compact-action" disabled={loading} onClick={() => setSelectedRole(null)}>
                {c.switchRole}
              </button>
            </div>
            <label className="field">
              <span>{c.name}</span>
              <input data-testid="auth-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Alex Morgan" />
            </label>
            <label className="field">
              <span>{c.email}</span>
              <input data-testid="auth-email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="alex@example.com" />
            </label>
            <label className="field">
              <span>{c.phoneNumber}</span>
              <input data-testid="auth-phone" value={phoneNumber} onChange={(event) => setPhoneNumber(event.target.value)} placeholder={c.phoneHint} />
            </label>
            <label className="field">
              <span>{c.password}</span>
              <input data-testid="auth-password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder={c.passwordHint} />
            </label>
            <div className="two-column-fields">
              <label className="field">
                <span>{c.language}</span>
                <select value={language} onChange={(event) => setLanguage(event.target.value as SupportedLanguage)}>
                  {LANGUAGE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>{c.verifyBy}</span>
                <select value={verificationChannel} onChange={(event) => setVerificationChannel(event.target.value as "email" | "sms" | "whatsapp")}>
                  <option value="email">Email</option>
                  <option value="sms">SMS</option>
                  <option value="whatsapp">WhatsApp</option>
                </select>
              </label>
            </div>
            {error ? (
              <div className="error" role="alert">
                <strong>{c.sessionIssue}</strong>
                <span>{error}</span>
              </div>
            ) : null}
            <div className="role-actions">
              <button className="primary-action" data-testid="auth-continue" disabled={!canLogin} onClick={() => selectedRole && onLogin(selectedRole)}>
                {loading ? <span className="spinner" /> : null}
                {c.continueAs} {selectedRoleLabel}
              </button>
            </div>
          </>
        )}
      </div>
      {!selectedRole ? (
        <div className="panel market-panel">
          <div className="panel-header">
            <div>
              <h2>{c.marketPreviewTitle}</h2>
              <p>{c.marketPreviewHelp}</p>
            </div>
          </div>
          <label className="field">
            <span>{c.searchJobs}</span>
            <input value={jobSearch} onChange={(event) => setJobSearch(event.target.value)} placeholder={c.jobSearchPlaceholder} />
          </label>
          <label className="field">
            <span>{c.targetMarket}</span>
            <select value={targetMarket} onChange={(event) => setTargetMarket(event.target.value as TargetMarket)}>
              {MARKET_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {c[option.labelKey]}
                </option>
              ))}
            </select>
          </label>
          <div className="market-signal-grid">
            <span>{marketJobs.length} · {c.openRoles}</span>
            <span>{c.remoteFriendly}</span>
            <span>{c.salarySignal}</span>
            <span>{c.localHiring}</span>
          </div>
          <div className="job-preview-list">
            {visiblePreviewJobs.length ? (
              visiblePreviewJobs.map((job) => (
                <div className="job-preview-card" key={job.role}>
                  <div>
                    <strong>{job.role}</strong>
                    <p>{job.signal}</p>
                  </div>
                  <span>{job.demand}%</span>
                </div>
              ))
            ) : (
              <p className="empty-preview">{c.noMarketMatch}</p>
            )}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function CandidateDashboard({ user, c }: { user: User; c: Copy }) {
  const [profile, setProfile] = useState<CandidateProfile>({
    id: 0,
    user_id: user.id,
    headline: "",
    skills: "",
    experience: "",
    education: "",
    portfolio_url: "",
    github_url: "",
    linkedin_url: "",
    project_demo_urls: "",
    visibility: "private",
    bio: "",
  });
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<JobPost[]>([]);
  const [matches, setMatches] = useState<Analysis[]>([]);
  const [metrics, setMetrics] = useState<CandidateMetrics | null>(null);
  const [resumeId, setResumeId] = useState("");
  const [jobPostId, setJobPostId] = useState("");
  const [resumeTitle, setResumeTitle] = useState("Primary resume");
  const [resumeText, setResumeText] = useState(sampleResume);
  const [current, setCurrent] = useState<Analysis | null>(null);
  const [interview, setInterview] = useState<InterviewPractice | null>(null);
  const [coach, setCoach] = useState<CareerCoachPlan | null>(null);
  const [salary, setSalary] = useState<SalaryIntelligence | null>(null);
  const [github, setGithub] = useState<GitHubAnalysis | null>(null);
  const [githubUrl, setGithubUrl] = useState("https://github.com/your-username");
  const [loading, setLoading] = useState(false);
  const [activeTool, setActiveTool] = useState<"interview" | "coach" | "salary" | "github" | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    refreshCandidate();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id]);

  async function refreshCandidate() {
    setError("");
    try {
      const [nextProfile, nextResumes, nextJobs, nextMatches, nextMetrics] = await Promise.all([
        getCandidateProfile(user),
        listResumes(user),
        listJobPosts(),
        listMatches(user),
        getCandidateMetrics(user),
      ]);
      setProfile(nextProfile);
      setResumes(nextResumes);
      setJobs(nextJobs);
      setMatches(nextMatches);
      setMetrics(nextMetrics);
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
    const saved = await saveCandidateProfile(user, profile);
    setProfile(saved);
    setNotice(user.language === "es" ? "Perfil guardado." : "Candidate profile saved.");
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
      setNotice(user.language === "es" ? "Resume guardado en tu cuenta." : "Resume saved to your candidate account.");
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
      setNotice(user.language === "es" ? "Texto extraido. Guardalo para conectarlo a tu perfil." : "Resume text extracted. Save it to attach it to your profile.");
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
      setNotice(user.language === "es" ? "Match creado con tu resume y el empleo seleccionado." : "Match created from your resume and selected job post.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create match.");
    } finally {
      setLoading(false);
    }
  }

  async function runCandidateTool(tool: "interview" | "coach" | "salary" | "github") {
    setLoading(true);
    setActiveTool(tool);
    setError("");
    setNotice("");
    try {
      const selectedResumeId = resumeId ? Number(resumeId) : undefined;
      const currentResumeText = resumeText.trim();
      if (tool === "interview") {
        const result = await practiceInterview(user, selectedResumeId, currentResumeText);
        setInterview(result);
        setNotice(user.language === "es" ? "Entrevista de practica generada." : "Practice interview generated.");
      } else if (tool === "coach") {
        const result = await getCareerCoachPlan(user, selectedResumeId, jobPostId ? Number(jobPostId) : undefined, currentResumeText);
        setCoach(result);
        setNotice(user.language === "es" ? "Roadmap de carrera generado." : "Career roadmap generated.");
      } else if (tool === "salary") {
        if (!selectedResumeId && currentResumeText.length < 20) throw new Error(user.language === "es" ? "Pega o sube un resume primero." : "Paste or upload a resume first.");
        const result = await getSalaryIntelligence(user, selectedResumeId, currentResumeText);
        setSalary(result);
        setNotice(user.language === "es" ? "Estimacion salarial generada." : "Salary estimate generated.");
      } else {
        const candidateGithubUrl = githubUrl.trim() || profile.github_url.trim();
        if (!candidateGithubUrl) throw new Error(user.language === "es" ? "Agrega una URL de GitHub primero." : "Add a GitHub URL first.");
        const result = await analyzeGitHub(user, candidateGithubUrl);
        setGithub(result);
        setGithubUrl(candidateGithubUrl);
        setNotice(user.language === "es" ? "Analisis de GitHub generado." : "GitHub analysis generated.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not run AI tool.");
    } finally {
      setLoading(false);
      setActiveTool(null);
    }
  }

  return (
    <>
      <DashboardMetrics latest={current} itemCount={resumes.length} itemLabel={c.savedResumes} matchCount={matches.length} mode={c.candidate} c={c} language={user.language} />
      <SaaSMetrics
        items={[
          [c.applications, String(metrics?.applications ?? 0)],
          [c.averageMatch, `${metrics?.average_match_score ?? 0}%`],
          [c.profileStrength, `${metrics?.profile_strength ?? 0}%`],
        ]}
      />
      <section className="workspace role-workspace">
        <div className="panel input-panel">
          <PanelTitle title={c.candidateProfile} subtitle={c.candidateProfileHelp} />
          <label className="field">
            <span>{c.headline}</span>
            <input value={profile.headline} onChange={(event) => setProfile({ ...profile, headline: event.target.value })} />
          </label>
          <label className="field">
            <span>{c.skills}</span>
            <input value={profile.skills} onChange={(event) => setProfile({ ...profile, skills: event.target.value })} />
          </label>
          <label className="field">
            <span>{c.bio}</span>
            <textarea value={profile.bio} onChange={(event) => setProfile({ ...profile, bio: event.target.value })} />
          </label>
          <div className="proof-section">
            <PanelTitle title={c.proofOfWork} subtitle={c.proofOfWorkHelp} />
            <label className="field">
              <span>{c.portfolioUrl}</span>
              <input value={profile.portfolio_url} onChange={(event) => setProfile({ ...profile, portfolio_url: event.target.value })} placeholder="https://your-portfolio.com" />
            </label>
            <label className="field">
              <span>{c.githubProfile}</span>
              <input value={profile.github_url} onChange={(event) => setProfile({ ...profile, github_url: event.target.value })} placeholder="https://github.com/your-username" />
            </label>
            <label className="field">
              <span>{c.linkedinProfile}</span>
              <input value={profile.linkedin_url} onChange={(event) => setProfile({ ...profile, linkedin_url: event.target.value })} placeholder="https://linkedin.com/in/your-name" />
            </label>
            <label className="field">
              <span>{c.projectDemos}</span>
              <textarea
                className="compact-textarea"
                value={profile.project_demo_urls}
                onChange={(event) => setProfile({ ...profile, project_demo_urls: event.target.value })}
                placeholder={c.projectDemosHint}
              />
            </label>
            <ProofLinks profile={profile} c={c} />
          </div>
          <label className="field">
            <span>{c.visibility}</span>
            <select value={profile.visibility} onChange={(event) => setProfile({ ...profile, visibility: event.target.value as CandidateProfile["visibility"] })}>
              <option value="private">{c.private}</option>
              <option value="visible_to_verified_recruiters">{c.verifiedRecruiters}</option>
              <option value="public">{c.public}</option>
            </select>
          </label>
          <button className="secondary-action" onClick={onSaveProfile}>{c.saveProfile}</button>
        </div>

        <div className="panel input-panel">
          <PanelTitle title={c.myResume} subtitle={c.myResumeHelp} />
          <label className="field">
            <span>{c.existingResume}</span>
            <select value={resumeId} onChange={(event) => {
              const selected = resumes.find((resume) => resume.id === Number(event.target.value));
              setResumeId(event.target.value);
              if (selected) {
                setResumeTitle(selected.title);
                setResumeText(selected.resume_text);
              }
            }}>
              <option value="">{c.createResume}</option>
              {resumes.map((resume) => <option key={resume.id} value={resume.id}>{resume.title}</option>)}
            </select>
          </label>
          <label className="field">
            <span>{c.resumeTitle}</span>
            <input data-testid="resume-title" value={resumeTitle} onChange={(event) => setResumeTitle(event.target.value)} />
          </label>
          <label className="file-button inline-upload">
            {c.uploadResume}
            <input type="file" accept=".txt,.pdf,text/plain,application/pdf" onChange={onFileChange} />
          </label>
          <label className="field">
            <span>{c.resumeText}</span>
            <textarea data-testid="resume-text" value={resumeText} onChange={(event) => setResumeText(event.target.value)} />
          </label>
          <button className="primary-action" data-testid="save-resume" disabled={loading || resumeText.trim().length < 20} onClick={onSaveResume}>
            {loading ? <span className="spinner" /> : null}
            {c.saveResume}
          </button>
        </div>

        <div className="panel result-panel">
          <PanelTitle title={c.jobMatches} subtitle={c.jobMatchesHelp} />
          <label className="field">
            <span>{c.resume}</span>
            <select value={resumeId} onChange={(event) => setResumeId(event.target.value)}>
              <option value="">{c.selectResume}</option>
              {resumes.map((resume) => <option key={resume.id} value={resume.id}>{resume.title}</option>)}
            </select>
          </label>
          <label className="field">
            <span>{c.jobPost}</span>
            <select value={jobPostId} onChange={(event) => setJobPostId(event.target.value)}>
              <option value="">{c.selectJob}</option>
              {jobs.map((job) => <option key={job.id} value={job.id}>{job.title} - {job.company || c.unknownCompany}</option>)}
            </select>
          </label>
          <button className="primary-action" disabled={loading || !resumeId || !jobPostId} onClick={onRunMatch}>
            {loading ? <span className="spinner" /> : null}
            {c.runMatch}
          </button>
          <StatusMessages error={error} notice={notice} c={c} />
          {jobPostId ? <button className="secondary-action" onClick={async () => {
            try {
              await reportJobPost(user, Number(jobPostId), "This job post looks suspicious and needs review.");
              setNotice(user.language === "es" ? "Empleo reportado para revision." : "Job reported for admin review.");
            } catch (err) {
              setError(err instanceof Error ? err.message : "Could not report job.");
            }
          }}>{c.reportJob}</button> : null}
          <MatchResult result={current} c={c} language={user.language} />
        </div>
      </section>
      <section className="panel history-wide">
        <PanelTitle title={c.aiTools} subtitle={c.aiToolsHelp} />
        <div className="tool-grid">
          <button className="secondary-action" data-testid="practice-interview" disabled={loading} onClick={() => runCandidateTool("interview")}>
            {activeTool === "interview" ? <span className="spinner" /> : null}
            {c.practiceInterview}
          </button>
          <button className="secondary-action" disabled={loading} onClick={() => runCandidateTool("coach")}>
            {activeTool === "coach" ? <span className="spinner" /> : null}
            {c.careerCoach}
          </button>
          <button className="secondary-action" disabled={loading || (!resumeId && resumeText.trim().length < 20)} onClick={() => runCandidateTool("salary")}>
            {activeTool === "salary" ? <span className="spinner" /> : null}
            {c.salaryIntel}
          </button>
          <label className="field github-field">
            <span>{c.githubUrl}</span>
            <input value={githubUrl} onChange={(event) => setGithubUrl(event.target.value)} placeholder="https://github.com/your-username" />
          </label>
          <button className="secondary-action" disabled={loading} onClick={() => runCandidateTool("github")}>
            {activeTool === "github" ? <span className="spinner" /> : null}
            {c.githubAnalysis}
          </button>
        </div>
        <StatusMessages error={error} notice={notice} c={c} />
        <CandidateInsights interview={interview} coach={coach} salary={salary} github={github} c={c} />
      </section>
      <MatchHistory matches={matches} setCurrent={setCurrent} c={c} language={user.language} />
    </>
  );
}

function CandidateInsights({
  interview,
  coach,
  salary,
  github,
  c,
}: {
  interview: InterviewPractice | null;
  coach: CareerCoachPlan | null;
  salary: SalaryIntelligence | null;
  github: GitHubAnalysis | null;
  c: Copy;
}) {
  if (!interview && !coach && !salary && !github) return <p className="empty">{c.noResults}</p>;
  return (
    <div className="insight-grid">
      {interview ? (
        <div className="insight-card">
          <strong>{c.interviewScore}: {interview.interview_score}/100</strong>
          <p>{interview.feedback}</p>
          <h3>{c.strengths}</h3>
          <ul>{interview.strengths.map((item) => <li key={item}>+ {item}</li>)}</ul>
          <h3>{c.needsImprovement}</h3>
          <ul>{interview.needs_improvement.map((item) => <li key={item}>- {item}</li>)}</ul>
          <h3>Questions</h3>
          <ul>{interview.questions.slice(0, 4).map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      ) : null}
      {coach ? (
        <div className="insight-card">
          <strong>{coach.current_score}% to {coach.target_score}%</strong>
          <h3>{c.learn}</h3>
          <ul>{coach.learn.map((item) => <li key={item}>{item}</li>)}</ul>
          <p><b>{c.estimatedEffort}:</b> {coach.estimated_effort}</p>
          <h3>{c.roadmap}</h3>
          <ul>{coach.roadmap.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      ) : null}
      {salary ? (
        <div className="insight-card">
          <strong>{c.salaryRanges}</strong>
          <ul>{salary.ranges.map((item) => <li key={item.market}>{item.market}: {item.range}</li>)}</ul>
          <p>{salary.rationale}</p>
        </div>
      ) : null}
      {github ? (
        <div className="insight-card">
          <strong>{c.portfolioScore}: {github.portfolio_score}/100</strong>
          <p>{github.commit_frequency}</p>
          <h3>Languages</h3>
          <p>{github.languages.join(", ")}</p>
          <h3>Projects</h3>
          <p>{github.projects.join(", ")}</p>
          <h3>{c.recommendations}</h3>
          <ul>{github.recommendations.map((item) => <li key={item}>{item}</li>)}</ul>
        </div>
      ) : null}
    </div>
  );
}

function normalizeUrl(url: string): string {
  const trimmed = url.trim();
  if (!trimmed) return "";
  return /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
}

function ProofLinks({ profile, c }: { profile: CandidateProfile; c: Copy }) {
  const demos = profile.project_demo_urls
    .split(/\r?\n/)
    .map(normalizeUrl)
    .filter(Boolean)
    .slice(0, 4);
  const links = [
    [c.openPortfolio, normalizeUrl(profile.portfolio_url)],
    [c.openGitHub, normalizeUrl(profile.github_url)],
    [c.openLinkedIn, normalizeUrl(profile.linkedin_url)],
    ...demos.map((url, index) => [`${c.openDemo} ${index + 1}`, url] as [string, string]),
  ].filter(([, url]) => url);

  if (!links.length) return null;

  return (
    <div className="proof-links">
      {links.map(([label, url]) => (
        <a key={`${label}-${url}`} href={url} target="_blank" rel="noreferrer">
          {label}
        </a>
      ))}
    </div>
  );
}

function AdminDashboard({ user, c }: { user: User; c: Copy }) {
  const [companies, setCompanies] = useState<RecruiterProfile[]>([]);
  const [flaggedJobs, setFlaggedJobs] = useState<JobPost[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    refreshAdmin();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id]);

  async function refreshAdmin() {
    setError("");
    try {
      const [nextCompanies, nextFlaggedJobs] = await Promise.all([
        listAdminCompanies(user),
        listAdminFlaggedJobs(user),
      ]);
      setCompanies(nextCompanies);
      setFlaggedJobs(nextFlaggedJobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load admin review.");
    }
  }

  async function reviewCompany(recruiterUserId: number, status: "verified" | "rejected") {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      await reviewAdminCompany(user, recruiterUserId, status);
      await refreshAdmin();
      setNotice(status === "verified" ? "Company approved." : "Company rejected.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not review company.");
    } finally {
      setLoading(false);
    }
  }

  async function removeJob(jobPostId: number) {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      await removeAdminJob(user, jobPostId);
      await refreshAdmin();
      setNotice("Flagged job removed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove job.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <section className="workspace role-workspace">
        <div className="panel input-panel">
          <PanelTitle title={c.companiesForReview} subtitle={c.adminPerms} />
          {companies.length ? companies.map((company) => (
            <div className="history-card" key={company.user_id}>
              <div>
                <strong>{company.company || c.unknownCompany}</strong>
                <p>{company.website || company.contact_email || company.description || c.noResults}</p>
              </div>
              <div className="trust-strip">
                <span>{c.status}: {company.company_status}</span>
                <span>{c.trust}: {company.trust_score}/100</span>
              </div>
              <div className="role-actions">
                <button className="secondary-action compact-action" disabled={loading} onClick={() => reviewCompany(company.user_id, "verified")}>
                  {c.approve}
                </button>
                <button className="secondary-action compact-action" disabled={loading} onClick={() => reviewCompany(company.user_id, "rejected")}>
                  {c.reject}
                </button>
              </div>
            </div>
          )) : <p className="empty">{c.noCompanies}</p>}
        </div>

        <div className="panel result-panel">
          <PanelTitle title={c.flaggedJobs} subtitle={c.actionBlocked} />
          {flaggedJobs.length ? flaggedJobs.map((job) => (
            <div className="history-card" key={job.id}>
              <div>
                <strong>{job.title}</strong>
                <p>{job.company || c.unknownCompany} · {job.location || job.work_mode}</p>
              </div>
              <div className="trust-strip">
                <span>{c.spam}: {job.spam_score}/100</span>
                <span>{c.quality}: {job.quality_score}/100</span>
                <span>{c.status}: {job.status}</span>
              </div>
              <button className="secondary-action compact-action" disabled={loading} onClick={() => removeJob(job.id)}>
                {c.removeJob}
              </button>
            </div>
          )) : <p className="empty">{c.noFlaggedJobs}</p>}
        </div>
      </section>
      <StatusMessages error={error} notice={notice} c={c} />
    </>
  );
}

function RecruiterDashboard({ user, c }: { user: User; c: Copy }) {
  const [account, setAccount] = useState<User>(user);
  const [profile, setProfile] = useState<RecruiterProfile>({
    id: 0,
    user_id: user.id,
    company: "",
    title: "",
    website: "",
    country: "",
    city: "",
    industry: "",
    company_size: "",
    description: "",
    contact_email: "",
    company_status: "pending_review",
    trust_score: 0,
  });
  const [jobs, setJobs] = useState<JobPost[]>([]);
  const [matches, setMatches] = useState<Analysis[]>([]);
  const [metrics, setMetrics] = useState<RecruiterMetrics | null>(null);
  const [jobId, setJobId] = useState("");
  const [jobTitle, setJobTitle] = useState("Software Engineer");
  const [company, setCompany] = useState("Acme");
  const [location, setLocation] = useState("");
  const [workMode, setWorkMode] = useState<JobPost["work_mode"]>("remote");
  const [salaryRange, setSalaryRange] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("");
  const [requiredSkills, setRequiredSkills] = useState("Python, FastAPI, React, Docker, SQL");
  const [niceToHaveSkills, setNiceToHaveSkills] = useState("AWS, GitHub Actions");
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
      const [nextProfile, nextJobs, nextMatches, nextMetrics] = await Promise.all([
        getRecruiterProfile(user),
        listMyJobPosts(user),
        listMatches(user),
        getRecruiterMetrics(user),
      ]);
      setProfile(nextProfile);
      setJobs(nextJobs);
      setMatches(nextMatches);
      setMetrics(nextMetrics);
      setJobId(nextJobs[0] ? String(nextJobs[0].id) : "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load recruiter workspace.");
    }
  }

  function loadJobIntoForm(selected?: JobPost) {
    if (!selected) {
      setJobTitle("Software Engineer");
      setCompany(profile.company || "Acme");
      setLocation("");
      setWorkMode("remote");
      setSalaryRange("");
      setExperienceLevel("");
      setRequiredSkills("Python, FastAPI, React, Docker, SQL");
      setNiceToHaveSkills("AWS, GitHub Actions");
      setDescription(sampleJob);
      return;
    }
    setJobTitle(selected.title);
    setCompany(selected.company);
    setLocation(selected.location);
    setWorkMode(selected.work_mode);
    setSalaryRange(selected.salary_range);
    setExperienceLevel(selected.experience_level);
    setRequiredSkills(selected.required_skills);
    setNiceToHaveSkills(selected.nice_to_have_skills);
    setDescription(selected.description);
  }

  async function onSaveProfile() {
    setError("");
    setNotice("");
    const saved = await saveRecruiterProfile(user, profile);
    setProfile(saved);
    setNotice("Recruiter profile saved.");
  }

  async function onVerifyAccount() {
    setError("");
    setNotice("");
    try {
      const verified = await verifyAccount(account);
      setAccount(verified);
      setNotice("Account marked verified. Company review is still required before publishing.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not verify account.");
    }
  }

  async function onSaveJob() {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const jobInput: JobPostInput = {
        title: jobTitle,
        company,
        location,
        work_mode: workMode,
        salary_range: salaryRange,
        experience_level: experienceLevel,
        required_skills: requiredSkills,
        nice_to_have_skills: niceToHaveSkills,
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

  async function onPublishJob() {
    if (!jobId) return;
    setLoading(true);
    setError("");
    setNotice("");
    try {
      await publishJobPost(account, Number(jobId));
      await refreshRecruiter();
      setNotice("Job published.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not publish job.");
    } finally {
      setLoading(false);
    }
  }

  const latest = matches[0] ?? null;

  return (
    <>
      <DashboardMetrics latest={latest} itemCount={jobs.length} itemLabel={c.myJobPosts} matchCount={matches.length} mode={c.recruiter} c={c} language={user.language} />
      <SaaSMetrics
        items={[
          [c.candidatesApplied, String(metrics?.candidates_applied ?? 0)],
          [c.averageMatch, `${metrics?.average_match_score ?? 0}%`],
          [c.interviewsScheduled, String(metrics?.interviews_scheduled ?? 0)],
        ]}
      />
      <section className="workspace role-workspace">
        <div className="panel input-panel">
          <PanelTitle title={c.recruiterProfile} subtitle={c.recruiterProfileHelp} />
          <label className="field">
            <span>{c.company}</span>
            <input value={profile.company} onChange={(event) => setProfile({ ...profile, company: event.target.value })} />
          </label>
          <label className="field">
            <span>{c.headline}</span>
            <input value={profile.title} onChange={(event) => setProfile({ ...profile, title: event.target.value })} />
          </label>
          <label className="field">
            <span>{c.website}</span>
            <input value={profile.website} onChange={(event) => setProfile({ ...profile, website: event.target.value })} placeholder="https://company.com" />
          </label>
          <label className="field">
            <span>{c.contactEmail}</span>
            <input value={profile.contact_email} onChange={(event) => setProfile({ ...profile, contact_email: event.target.value })} placeholder="jobs@company.com" />
          </label>
          <div className="two-column-fields">
            <label className="field">
              <span>{c.country}</span>
              <input value={profile.country} onChange={(event) => setProfile({ ...profile, country: event.target.value })} />
            </label>
            <label className="field">
              <span>{c.city}</span>
              <input value={profile.city} onChange={(event) => setProfile({ ...profile, city: event.target.value })} />
            </label>
          </div>
          <label className="field">
            <span>{c.companyDescription}</span>
            <textarea value={profile.description} onChange={(event) => setProfile({ ...profile, description: event.target.value })} />
          </label>
          <div className="trust-strip">
            <span>{c.email}: {account.verification_status}</span>
            <span>{c.company}: {profile.company_status}</span>
            <span>{c.trust}: {profile.trust_score}/100</span>
          </div>
          <button className="secondary-action" onClick={onVerifyAccount}>{c.verifyAccount}</button>
          <button className="secondary-action" onClick={onSaveProfile}>{c.saveProfile}</button>
        </div>

        <div className="panel input-panel">
          <PanelTitle title={c.myJobPosts} subtitle={c.recruiterPerms} />
          <label className="field">
            <span>{c.jobPost}</span>
            <select value={jobId} onChange={(event) => {
              const selected = jobs.find((job) => job.id === Number(event.target.value));
              setJobId(event.target.value);
              loadJobIntoForm(selected);
            }}>
              <option value="">{c.createJob}</option>
              {jobs.map((job) => <option key={job.id} value={job.id}>{job.title}</option>)}
            </select>
          </label>
          <label className="field">
            <span>{c.headline}</span>
            <input data-testid="job-title" value={jobTitle} onChange={(event) => setJobTitle(event.target.value)} />
          </label>
          <label className="field">
            <span>{c.company}</span>
            <input data-testid="job-company" value={company} onChange={(event) => setCompany(event.target.value)} />
          </label>
          <div className="two-column-fields">
            <label className="field">
              <span>{c.location}</span>
              <input data-testid="job-location" value={location} onChange={(event) => setLocation(event.target.value)} placeholder="Quito, Ecuador" />
            </label>
            <label className="field">
              <span>{c.workMode}</span>
              <select value={workMode} onChange={(event) => setWorkMode(event.target.value as JobPost["work_mode"])}>
                <option value="remote">{c.remote}</option>
                <option value="hybrid">{c.hybrid}</option>
                <option value="onsite">{c.onsite}</option>
              </select>
            </label>
          </div>
          <div className="two-column-fields">
            <label className="field">
              <span>{c.salaryRange}</span>
              <input data-testid="job-salary" value={salaryRange} onChange={(event) => setSalaryRange(event.target.value)} placeholder="$1200-$1800" />
            </label>
            <label className="field">
              <span>{c.experienceLevel}</span>
              <input data-testid="job-experience" value={experienceLevel} onChange={(event) => setExperienceLevel(event.target.value)} placeholder="Junior, Mid, Senior" />
            </label>
          </div>
          <label className="field">
            <span>{c.requiredSkills}</span>
            <input data-testid="job-required-skills" value={requiredSkills} onChange={(event) => setRequiredSkills(event.target.value)} placeholder="Python, FastAPI, SQL" />
          </label>
          <label className="field">
            <span>{c.niceToHaveSkills}</span>
            <input data-testid="job-nice-skills" value={niceToHaveSkills} onChange={(event) => setNiceToHaveSkills(event.target.value)} placeholder="AWS, CI/CD, Docker" />
          </label>
          <label className="field">
            <span>{c.companyDescription}</span>
            <textarea data-testid="job-description" value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <button className="primary-action" data-testid="save-job" disabled={loading || description.trim().length < 20} onClick={onSaveJob}>
            {loading ? <span className="spinner" /> : null}
            {c.saveJob}
          </button>
          <button className="secondary-action" disabled={loading || !jobId} onClick={onPublishJob}>{c.publishJob}</button>
          {jobs.find((job) => job.id === Number(jobId)) ? (
            <div className="trust-strip">
              <span>{c.status}: {jobs.find((job) => job.id === Number(jobId))?.status}</span>
              <span>{c.quality}: {jobs.find((job) => job.id === Number(jobId))?.quality_score}/100</span>
              <span>{c.spam}: {jobs.find((job) => job.id === Number(jobId))?.spam_score}/100</span>
            </div>
          ) : null}
          <StatusMessages error={error} notice={notice} c={c} />
        </div>

        <div className="panel result-panel">
          <PanelTitle title={c.candidateResults} subtitle={c.candidateResultsHelp} />
          <MatchResult result={latest} c={c} language={user.language} />
        </div>
      </section>
      <MatchHistory matches={matches} setCurrent={() => undefined} c={c} language={user.language} />
    </>
  );
}

function DashboardMetrics({ latest, itemCount, itemLabel, matchCount, mode, c, language }: { latest: Analysis | null; itemCount: number; itemLabel: string; matchCount: number; mode: string; c: Copy; language: SupportedLanguage }) {
  const average = useMemo(() => latest?.match_score ?? 0, [latest]);
  return (
    <section className="metrics-grid">
      <div className="metric">
        <span>{c.latestScore}</span>
        <strong>{latest ? latest.match_score : "--"}</strong>
        <small>{latest ? scoreLabel(latest.match_score, language) : c.noMatchYet}</small>
      </div>
      <div className="metric">
        <span>{itemLabel}</span>
        <strong>{itemCount}</strong>
        <small>{c.ownedBySession}</small>
      </div>
      <div className="metric">
        <span>{c.matches}</span>
        <strong>{matchCount}</strong>
        <small>{c.roleFiltered}</small>
      </div>
      <div className="metric">
        <span>{c.workspace}</span>
        <strong>{mode}</strong>
        <small>{average ? `${average}/100` : c.accessControlled}</small>
      </div>
    </section>
  );
}

function SaaSMetrics({ items }: { items: [string, string][] }) {
  return (
    <section className="saas-metrics">
      {items.map(([label, value]) => (
        <div className="saas-metric" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
      ))}
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

function StatusMessages({ error, notice, c }: { error: string; notice: string; c: Copy }) {
  return (
    <>
      {error ? (
        <div className="error" role="alert">
          <strong>{c.actionBlocked}</strong>
          <span>{error}</span>
        </div>
      ) : null}
      {notice ? <div className="notice">{notice}</div> : null}
    </>
  );
}

function MatchResult({ result, c, language }: { result: Analysis | null; c: Copy; language: SupportedLanguage }) {
  if (!result) return <p className="empty">{c.noResults}</p>;

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
          <small>{scoreLabel(result.match_score, language)}</small>
        </div>
      </div>
      <p className="summary">{result.summary}</p>
      <div className="section-title">
        <h3>{c.skillGaps}</h3>
        <span>{result.missing_skills.length} {c.gaps}</span>
      </div>
      <div className="skill-bars">
        {result.missing_skills.length ? (
          result.missing_skills.slice(0, 6).map((skill, index) => {
            const impact = Math.max(38, 92 - index * 8);
            return (
              <div className="skill-gap" key={skill}>
                <div>
                  <span>{skill}</span>
                  <strong>{impact}%</strong>
                </div>
                <div className="gap-track">
                  <span style={{ width: `${impact}%` }} />
                </div>
              </div>
            );
          })
        ) : (
          <div className="no-gap">{c.noGaps}</div>
        )}
      </div>
      <div className="section-title">
        <h3>{c.improvements}</h3>
        <span>{result.improvements.length} {c.actions}</span>
      </div>
      <ul className="improvements">
        {result.improvements.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}

function MatchHistory({ matches, setCurrent, c, language }: { matches: Analysis[]; setCurrent: (analysis: Analysis) => void; c: Copy; language: SupportedLanguage }) {
  return (
    <section className="panel history-wide">
      <PanelTitle title={c.history} subtitle={c.historyHelp} />
      <div className="history-list horizontal-history">
        {matches.length ? matches.map((item) => (
          <button key={item.id} className="history-item" onClick={() => setCurrent(item)}>
            <div>
              <span>{new Date(item.created_at).toLocaleString()}</span>
              <small>{scoreLabel(item.match_score, language)}</small>
            </div>
            <strong>{item.match_score}</strong>
          </button>
        )) : <p className="empty">{c.noResults}</p>}
      </div>
    </section>
  );
}
