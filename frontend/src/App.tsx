import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock3,
  Database,
  DollarSign,
  Eye,
  EyeOff,
  FileJson2,
  FileText,
  FileWarning,
  Gauge,
  Layers3,
  Loader2,
  LockKeyhole,
  RefreshCw,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  UploadCloud,
  Workflow,
  XCircle,
} from "lucide-react";
import { type FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";

import {
  API_BASE_URL,
  type AnalyticsDashboardResponse,
  type AuthUserResponse,
  type GeneratedReportResponse,
  type HealthResponse,
  type AuditLogResponse,
  type ExtractedRecordResponse,
  type ExtractionErrorResponse,
  type ParsedDocumentResponse,
  type ProcessingJobResponse,
  type SummaryReportResponse,
  type UploadedFileResponse,
  type ValidationErrorResponse,
  createReport,
  extractFile,
  getAnalyticsDashboard,
  getAuditLogs,
  getExtractionErrors,
  getRecords,
  getReportDownloadUrl,
  getReports,
  getHealth,
  getSummaryReport,
  getMe,
  login,
  parseFile,
  uploadFile,
} from "./api";

type UploadState = "idle" | "uploading" | "uploaded" | "error";
type IconComponent = typeof FileText;
type SectionId = "command-center" | "ingestion" | "jobs" | "records" | "reports" | "audit";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function cx(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

export default function App() {
  const [activeSection, setActiveSection] = useState<SectionId>("command-center");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedFile, setUploadedFile] = useState<UploadedFileResponse | null>(null);
  const [job, setJob] = useState<ProcessingJobResponse | null>(null);
  const [parsedDocument, setParsedDocument] = useState<ParsedDocumentResponse | null>(null);
  const [extractedRecord, setExtractedRecord] = useState<ExtractedRecordResponse | null>(null);
  const [records, setRecords] = useState<ExtractedRecordResponse[]>([]);
  const [validationErrors, setValidationErrors] = useState<ValidationErrorResponse[]>([]);
  const [generatedReports, setGeneratedReports] = useState<GeneratedReportResponse[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsDashboardResponse | null>(null);
  const [authUser, setAuthUser] = useState<AuthUserResponse | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogResponse[]>([]);
  const [extractionErrors, setExtractionErrors] = useState<ExtractionErrorResponse[]>([]);
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((error: Error) => setHealthError(error.message));
    void refreshObservability();
    void refreshWorkspaceData();
    void refreshAnalytics();
    void restoreAuthSession();
  }, []);

  async function restoreAuthSession() {
    const token = localStorage.getItem("vendorops_access_token");
    if (!token) return;
    try {
      setAuthUser(await getMe(token));
    } catch {
      localStorage.removeItem("vendorops_access_token");
      setAuthUser(null);
    }
  }

  async function handleLogin(email: string, password: string) {
    setAuthError(null);
    try {
      const result = await login(email, password);
      localStorage.setItem("vendorops_access_token", result.access_token);
      setAuthUser(result.user);
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Login failed.");
    }
  }

  function handleLogout() {
    localStorage.removeItem("vendorops_access_token");
    setAuthUser(null);
  }

  async function refreshAnalytics() {
    try {
      setAnalytics(await getAnalyticsDashboard());
    } catch {
      setAnalytics(null);
    }
  }

  async function refreshWorkspaceData() {
    try {
      const [recordList, reportList] = await Promise.all([getRecords(), getReports()]);
      setRecords(recordList);
      setGeneratedReports(reportList);
    } catch {
      setRecords([]);
      setGeneratedReports([]);
    }
  }

  async function refreshObservability() {
    try {
      const [logs, errors] = await Promise.all([getAuditLogs(), getExtractionErrors()]);
      setAuditLogs(logs);
      setExtractionErrors(errors);
    } catch {
      setAuditLogs([]);
      setExtractionErrors([]);
    }
  }

  const metrics = useMemo(
    () => [
      {
        label: "Documents processed",
        value: String(records.length),
        change: records.length > 0 ? "Available for reporting" : "Awaiting upload",
        icon: FileText,
      },
      {
        label: "Jobs queued",
        value: job ? "1" : "0",
        change: job ? "Pipeline request captured" : "No active jobs",
        icon: Workflow,
      },
      {
        label: "Parser status",
        value: extractedRecord ? "Ready" : "Idle",
        change: extractedRecord
          ? `${Math.round((extractedRecord.confidence ?? 0) * 100)}% extraction confidence`
          : "Extractor standby",
        icon: Gauge,
      },
      {
        label: "API status",
        value: health?.status === "ok" ? "Online" : "Check",
        change: health ? health.environment : healthError ?? "Connecting",
        icon: Server,
      },
    ],
    [extractedRecord, health, healthError, job, records.length],
  );

  async function handleUpload() {
    if (!selectedFile) {
      setFormError("Choose a PDF, CSV, TXT, or EML file before uploading.");
      return;
    }

    setFormError(null);
    setUploadState("uploading");
    setUploadedFile(null);
    setJob(null);
    setParsedDocument(null);
    setExtractedRecord(null);
    setValidationErrors([]);

    try {
      const uploaded = await uploadFile(selectedFile);
      setUploadedFile(uploaded);
      const [extraction, parsed] = await Promise.all([
        extractFile(uploaded.file_id),
        parseFile(uploaded.file_id),
      ]);
      setJob(extraction.job);
      setExtractedRecord(extraction.record);
      setRecords((currentRecords) => [extraction.record, ...currentRecords]);
      setValidationErrors(extraction.validation_errors);
      setParsedDocument(parsed);
      setUploadState("uploaded");
      void refreshObservability();
      void refreshWorkspaceData();
      void refreshAnalytics();
    } catch (error) {
      setUploadState("error");
      setFormError(error instanceof Error ? error.message : "Upload failed.");
      void refreshObservability();
    }
  }

  function handleNavigate(sectionId: SectionId) {
    setActiveSection(sectionId);
    document.getElementById(sectionId)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,#eff6ff_0,#f8fafc_34%,#ffffff_72%)] text-ink-900">
      <div className="mx-auto flex min-h-screen w-full max-w-[1500px] flex-col lg:flex-row">
        <Sidebar activeSection={activeSection} onNavigate={handleNavigate} />
        <main className="flex-1 px-4 py-4 sm:px-6 lg:px-8">
          <section id="command-center" className="scroll-mt-6">
            <TopBar health={health} healthError={healthError} />
          </section>

          <section className="mt-6">
            <SaaSIdentityPanel
              authUser={authUser}
              authError={authError}
              onLogin={(email, password) => void handleLogin(email, password)}
              onLogout={handleLogout}
            />
          </section>

          <section className="mt-6 grid scroll-mt-6 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {metrics.map((metric) => (
              <MetricCard key={metric.label} {...metric} />
            ))}
          </section>

          <section className="mt-6">
            <AnalystDashboard analytics={analytics} onRefresh={() => void refreshAnalytics()} />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
            <div id="ingestion" className="scroll-mt-6">
              <UploadPanel
                selectedFile={selectedFile}
                uploadState={uploadState}
                formError={formError}
                onFileSelect={setSelectedFile}
                onUpload={handleUpload}
              />
            </div>
            <div id="jobs" className="scroll-mt-6">
              <StatusPanel health={health} healthError={healthError} uploadedFile={uploadedFile} job={job} />
            </div>
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
            <div id="records" className="scroll-mt-6">
              <ExtractionPreview parsedDocument={parsedDocument} extractedRecord={extractedRecord} />
            </div>
            <div id="reports" className="scroll-mt-6">
              <ReportsPanel
                uploadedFile={uploadedFile}
                extractedRecord={extractedRecord}
                records={records}
                validationErrors={validationErrors}
                generatedReports={generatedReports}
                onReportGenerated={(report) =>
                  setGeneratedReports((currentReports) => [report, ...currentReports])
                }
              />
            </div>
          </section>

          <section id="audit" className="mt-6 scroll-mt-6">
            <ObservabilityPanel
              auditLogs={auditLogs}
              extractionErrors={extractionErrors}
              onRefresh={() => void refreshObservability()}
            />
          </section>
        </main>
      </div>
    </div>
  );
}

function Sidebar({
  activeSection,
  onNavigate,
}: {
  activeSection: SectionId;
  onNavigate: (sectionId: SectionId) => void;
}) {
  const navItems: Array<{ id: SectionId; label: string; icon: IconComponent }> = [
    { id: "command-center", label: "Command Center", icon: Layers3 },
    { id: "ingestion", label: "Ingestion", icon: UploadCloud },
    { id: "jobs", label: "Jobs", icon: Workflow },
    { id: "records", label: "Records", icon: Database },
    { id: "reports", label: "Reports", icon: BarChart3 },
    { id: "audit", label: "Audit", icon: ShieldCheck },
  ];

  return (
    <aside className="sticky top-0 hidden h-screen w-72 shrink-0 border-r border-cloud-200 bg-white/78 px-5 py-6 backdrop-blur-xl lg:block">
      <div className="flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-ink-950 text-white shadow-soft">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-wide text-ink-950">VendorOps AI</p>
          <p className="text-xs text-ink-500">Document intelligence</p>
        </div>
      </div>

      <nav className="mt-8 space-y-1">
        {navItems.map((item) => (
          <button
            key={item.label}
            type="button"
            aria-current={activeSection === item.id ? "page" : undefined}
            onClick={() => onNavigate(item.id)}
            className={cx(
              "group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
              activeSection === item.id
                ? "bg-ink-950 text-white shadow-soft"
                : "text-ink-500 hover:bg-cloud-100 hover:text-ink-900",
            )}
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="absolute bottom-6 left-5 right-5 rounded-lg border border-cloud-200 bg-cloud-50 p-4">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <LockKeyhole className="h-4 w-4 text-mint-600" />
          Audit-first pipeline
        </div>
        <p className="mt-2 text-xs leading-5 text-ink-500">
          Files, jobs, validation events, and reports are designed for traceable AI operations.
        </p>
      </div>
    </aside>
  );
}

function TopBar({ health, healthError }: { health: HealthResponse | null; healthError: string | null }) {
  return (
    <header className="rounded-xl border border-cloud-200 bg-white/82 p-4 shadow-line backdrop-blur-xl sm:p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-brand-500/15 bg-brand-500/10 px-3 py-1 text-xs font-semibold text-brand-700">
              AI Data Pipeline
            </span>
            <span className="rounded-full border border-mint-500/15 bg-mint-500/10 px-3 py-1 text-xs font-semibold text-mint-600">
              SQLite MVP
            </span>
          </div>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight text-ink-950 sm:text-3xl">
            Vendor document command center
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-500">
            Ingest contracts, invoices, CSVs, and emails, then turn messy source files into validated
            operational data for finance and procurement teams.
          </p>
        </div>

        <div className="flex min-w-[280px] items-center gap-3 rounded-lg border border-cloud-200 bg-cloud-50 px-4 py-3">
          <span
            className={cx(
              "h-2.5 w-2.5 rounded-full",
              health?.status === "ok"
                ? "bg-mint-500 shadow-[0_0_0_4px_rgba(16,185,129,0.14)]"
                : "bg-amber-500",
            )}
          />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-ink-900">
              {health?.status === "ok" ? "API connected" : "API status pending"}
            </p>
            <p className="truncate text-xs text-ink-500">{healthError ?? API_BASE_URL}</p>
          </div>
        </div>
      </div>
    </header>
  );
}

function MetricCard({
  label,
  value,
  change,
  icon: Icon,
}: {
  label: string;
  value: string;
  change: string;
  icon: IconComponent;
}) {
  return (
    <article className="rounded-xl border border-cloud-200 bg-white/86 p-5 shadow-line transition duration-200 hover:-translate-y-0.5 hover:shadow-soft">
      <div className="flex items-center justify-between">
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-cloud-100 text-ink-700">
          <Icon className="h-5 w-5" />
        </div>
        <Activity className="h-4 w-4 text-mint-500" />
      </div>
      <p className="mt-5 text-sm text-ink-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold tracking-tight text-ink-950">{value}</p>
      <p className="mt-2 text-xs font-medium text-ink-500">{change}</p>
    </article>
  );
}

function SaaSIdentityPanel({
  authUser,
  authError,
  onLogin,
  onLogout,
}: {
  authUser: AuthUserResponse | null;
  authError: string | null;
  onLogin: (email: string, password: string) => void;
  onLogout: () => void;
}) {
  const [email, setEmail] = useState("admin@vendorops.ai");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onLogin(email, password);
  }

  return (
    <section className="rounded-xl border border-cloud-200 bg-white p-5 shadow-soft sm:p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm font-semibold text-brand-700">SaaS foundation</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-ink-950">
            Tenant, workspace, and RBAC context
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-500">
            The platform now has seeded organization/workspace identity, password login, bearer
            sessions, roles, permissions, and protected context APIs.
          </p>
        </div>
        {authUser ? (
          <button
            className="rounded-lg border border-cloud-200 bg-white px-3 py-2 text-sm font-semibold text-ink-900 transition hover:bg-cloud-50"
            onClick={onLogout}
          >
            Sign out
          </button>
        ) : null}
      </div>

      {authError ? (
        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {authError}
        </div>
      ) : null}

      {!authUser ? (
        <form
          className="mt-5 grid gap-3 rounded-lg border border-cloud-200 bg-cloud-50 p-4 lg:grid-cols-[1fr_1fr_auto]"
          onSubmit={handleSubmit}
        >
          <label className="text-sm font-medium text-ink-700">
            Email
            <input
              className="mt-2 w-full rounded-lg border border-cloud-200 bg-white px-3 py-2 text-sm text-ink-900 outline-none transition focus:border-brand-500 focus:ring-4 focus:ring-brand-500/10"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>
          <label className="text-sm font-medium text-ink-700">
            Password
            <div className="mt-2 flex rounded-lg border border-cloud-200 bg-white focus-within:border-brand-500 focus-within:ring-4 focus-within:ring-brand-500/10">
              <input
                className="min-w-0 flex-1 rounded-l-lg bg-transparent px-3 py-2 text-sm text-ink-900 outline-none"
                type={showPassword ? "text" : "password"}
                value={password}
                placeholder="Enter password"
                autoComplete="current-password"
                onChange={(event) => setPassword(event.target.value)}
              />
              <button
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="grid w-11 place-items-center rounded-r-lg text-ink-500 transition hover:bg-cloud-50 hover:text-ink-900"
                type="button"
                onClick={() => setShowPassword((current) => !current)}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </label>
          <div className="flex items-end">
            <button className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-ink-950 px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:bg-ink-900">
              <LockKeyhole className="h-4 w-4" />
              Sign in
            </button>
          </div>
          <p className="text-xs leading-5 text-ink-500 lg:col-span-3">
            Demo owner email is prefilled for local testing. Keep the demo password private and
            replace seeded credentials in `.env` before a real deployment.
          </p>
        </form>
      ) : null}

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <InfoTile label="Organization" value={authUser?.organization.name ?? "Not signed in"} />
        <InfoTile label="Workspace" value={authUser?.workspace.name ?? "No workspace context"} />
        <InfoTile label="Role" value={authUser?.workspace.role ?? "Unauthenticated"} />
      </div>

      {authUser ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {authUser.permissions.map((permission) => (
            <span
              key={permission}
              className="rounded-full border border-brand-500/15 bg-brand-500/10 px-3 py-1 text-xs font-semibold text-brand-700"
            >
              {permission}
            </span>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function AnalystDashboard({
  analytics,
  onRefresh,
}: {
  analytics: AnalyticsDashboardResponse | null;
  onRefresh: () => void;
}) {
  const fallbackKpis = [
    { label: "Files processed today", value: "--", detail: "Waiting for analytics", trend: "loading", status: "watch" },
    { label: "Extraction accuracy", value: "--", detail: "No score loaded", trend: "loading", status: "watch" },
    { label: "Validation burden", value: "--", detail: "No findings loaded", trend: "loading", status: "watch" },
    { label: "Estimated LLM cost", value: "--", detail: "No cost loaded", trend: "loading", status: "watch" },
  ];
  const kpis = analytics?.kpis ?? fallbackKpis;
  const maxValidation = Math.max(
    1,
    ...((analytics?.validation_failures_by_document_type ?? []).map((item) => item.value)),
  );
  const maxErrors = Math.max(1, ...((analytics?.error_sources ?? []).map((item) => item.value)));
  const accuracyTrend = analytics?.extraction_accuracy_over_time ?? [];
  const latestAccuracy = accuracyTrend.length > 0 ? accuracyTrend[accuracyTrend.length - 1].value : 0;

  return (
    <section className="rounded-xl border border-cloud-200 bg-white p-5 shadow-soft sm:p-6">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-sm font-semibold text-brand-700">Executive intelligence</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-ink-950">
            Analyst-grade operations dashboard
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-ink-500">
            Tracks throughput, validation risk, retry pressure, extraction quality, cost exposure,
            and report demand from the operational data pipeline.
          </p>
        </div>
        <button
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-cloud-200 bg-white px-3 py-2 text-sm font-semibold text-ink-900 transition hover:bg-cloud-50"
          onClick={onRefresh}
        >
          <RefreshCw className="h-4 w-4" />
          Refresh analytics
        </button>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="rounded-lg border border-cloud-200 bg-cloud-50 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-semibold uppercase text-ink-500">{kpi.label}</p>
              <span
                className={cx(
                  "h-2.5 w-2.5 rounded-full",
                  kpi.status === "healthy" && "bg-mint-500",
                  kpi.status === "watch" && "bg-amber-500",
                  kpi.status === "risk" && "bg-red-500",
                )}
              />
            </div>
            <p className="mt-3 text-2xl font-semibold tracking-tight text-ink-950">{kpi.value}</p>
            <p className="mt-2 text-xs leading-5 text-ink-500">{kpi.detail}</p>
            <p className="mt-2 text-xs font-semibold text-brand-700">{kpi.trend}</p>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1fr_1fr_0.9fr]">
        <AnalystCard title="Validation failures by document type" icon={FileWarning}>
          <RankedBars
            items={analytics?.validation_failures_by_document_type ?? []}
            maxValue={maxValidation}
            emptyText="No validation failures recorded."
          />
        </AnalystCard>

        <AnalystCard title="Sources creating the most errors" icon={AlertTriangle}>
          <RankedBars
            items={analytics?.error_sources ?? []}
            maxValue={maxErrors}
            emptyText="No error sources detected."
          />
        </AnalystCard>

        <AnalystCard title="LLM cost and usage" icon={DollarSign}>
          <div className="rounded-lg bg-cloud-50 p-4">
            <p className="text-xs text-ink-500">Estimated cost</p>
            <p className="mt-1 text-2xl font-semibold text-ink-950">
              ${(analytics?.llm_cost.estimated_cost_usd ?? 0).toFixed(4)}
            </p>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <InfoTile
              label="Billable"
              value={String(analytics?.llm_cost.billable_records ?? 0)}
            />
            <InfoTile
              label="Mock"
              value={String(analytics?.llm_cost.mock_records ?? 0)}
            />
          </div>
        </AnalystCard>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_1fr]">
        <AnalystCard title="Extraction accuracy over time" icon={TrendingUp}>
          {analytics && analytics.extraction_accuracy_over_time.length > 0 ? (
            <div>
              <div className="flex items-end gap-2">
                {analytics.extraction_accuracy_over_time.map((point) => (
                  <div key={point.date} className="flex flex-1 flex-col items-center gap-2">
                    <div className="flex h-28 w-full items-end rounded-lg bg-cloud-50 px-1">
                      <div
                        className="w-full rounded-md bg-brand-600"
                        style={{ height: `${Math.max(6, point.value)}%` }}
                        title={`${point.date}: ${point.value}%`}
                      />
                    </div>
                    <span className="text-[10px] text-ink-500">{point.date.slice(5)}</span>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-sm text-ink-500">
                Latest average confidence: <span className="font-semibold text-ink-900">{latestAccuracy.toFixed(1)}%</span>
              </p>
            </div>
          ) : (
            <p className="rounded-lg bg-cloud-50 p-4 text-sm text-ink-500">No confidence trend yet.</p>
          )}
        </AnalystCard>

        <AnalystCard title="Blocked jobs and retry hotspots" icon={Target}>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <p className="mb-2 text-xs font-semibold uppercase text-ink-500">Blocked jobs</p>
              {analytics && analytics.blocked_jobs.length > 0 ? (
                <div className="space-y-2">
                  {analytics.blocked_jobs.slice(0, 4).map((job) => (
                    <div key={job.job_id} className="rounded-lg bg-cloud-50 p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-semibold text-ink-900">{job.status}</span>
                        <span className="text-xs text-ink-500">{job.age_hours.toFixed(1)}h</span>
                      </div>
                      <p className="mt-1 truncate text-xs text-ink-500">{job.error_message ?? job.job_id}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="rounded-lg bg-cloud-50 p-3 text-sm text-ink-500">No blocked jobs.</p>
              )}
            </div>
            <div>
              <p className="mb-2 text-xs font-semibold uppercase text-ink-500">Retry hotspots</p>
              <RankedBars
                items={analytics?.retry_hotspots ?? []}
                maxValue={Math.max(1, ...((analytics?.retry_hotspots ?? []).map((item) => item.value)))}
                emptyText="No retry hotspots."
              />
            </div>
          </div>
        </AnalystCard>
      </div>

      <div className="mt-4 rounded-lg border border-cloud-200 bg-ink-950 p-4 text-white">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-blue-200" />
          <p className="text-sm font-semibold">Analyst notes</p>
        </div>
        <div className="mt-3 grid gap-2 lg:grid-cols-2">
          {(analytics?.analyst_notes ?? ["Analytics are loading from the pipeline database."]).map((note) => (
            <p key={note} className="rounded-lg bg-white/5 p-3 text-sm leading-6 text-white/75">
              {note}
            </p>
          ))}
        </div>
      </div>
    </section>
  );
}

function AnalystCard({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: IconComponent;
  children: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-cloud-200 bg-white p-4 shadow-line">
      <div className="mb-4 flex items-center gap-2">
        <div className="grid h-8 w-8 place-items-center rounded-lg bg-cloud-100 text-ink-700">
          <Icon className="h-4 w-4" />
        </div>
        <p className="text-sm font-semibold text-ink-900">{title}</p>
      </div>
      {children}
    </div>
  );
}

function RankedBars({
  items,
  maxValue,
  emptyText,
}: {
  items: Array<{ label: string; value: number; detail?: string | null }>;
  maxValue: number;
  emptyText: string;
}) {
  if (items.length === 0) {
    return <p className="rounded-lg bg-cloud-50 p-4 text-sm text-ink-500">{emptyText}</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label}>
          <div className="mb-1 flex items-center justify-between gap-3">
            <p className="truncate text-sm font-semibold text-ink-900">{item.label}</p>
            <p className="text-sm font-semibold text-ink-700">{item.value}</p>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-cloud-100">
            <div
              className="h-full rounded-full bg-brand-600"
              style={{ width: `${Math.max(6, (item.value / maxValue) * 100)}%` }}
            />
          </div>
          {item.detail ? <p className="mt-1 text-xs text-ink-500">{item.detail}</p> : null}
        </div>
      ))}
    </div>
  );
}

function UploadPanel({
  selectedFile,
  uploadState,
  formError,
  onFileSelect,
  onUpload,
}: {
  selectedFile: File | null;
  uploadState: UploadState;
  formError: string | null;
  onFileSelect: (file: File | null) => void;
  onUpload: () => void;
}) {
  const isUploading = uploadState === "uploading";

  return (
    <section className="rounded-xl border border-cloud-200 bg-white p-5 shadow-soft sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-brand-700">Ingestion</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-ink-950">Upload source document</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-500">
            Accepts invoices, vendor CSVs, email exports, and contract PDFs. The API stores the file,
            creates a job, and normalizes parsed text for extraction.
          </p>
        </div>
        <span className="rounded-full bg-cloud-100 px-3 py-1 text-xs font-semibold text-ink-500">
          PDF / CSV / TXT / EML
        </span>
      </div>

      <label className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-cloud-200 bg-cloud-50 px-6 py-10 text-center transition hover:border-brand-500/50 hover:bg-brand-500/5">
        <div className="grid h-12 w-12 place-items-center rounded-lg bg-white text-brand-600 shadow-line">
          <UploadCloud className="h-6 w-6" />
        </div>
        <p className="mt-4 text-sm font-semibold text-ink-900">
          {selectedFile ? selectedFile.name : "Drop a document here or browse"}
        </p>
        <p className="mt-1 text-xs text-ink-500">
          {selectedFile ? formatBytes(selectedFile.size) : "Maximum clarity starts with clean ingestion."}
        </p>
        <input
          className="sr-only"
          type="file"
          accept=".pdf,.csv,.txt,.eml"
          onChange={(event) => onFileSelect(event.target.files?.[0] ?? null)}
        />
      </label>

      {formError ? (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{formError}</span>
        </div>
      ) : null}

      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-2 text-xs text-ink-500">
          <CheckCircle2 className="h-4 w-4 text-mint-600" />
          File hash, storage path, and audit events are captured.
        </div>
        <button
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-ink-950 px-4 py-2.5 text-sm font-semibold text-white shadow-soft transition hover:-translate-y-0.5 hover:bg-ink-900 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isUploading}
          onClick={onUpload}
        >
          {isUploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
          {isUploading ? "Processing" : "Upload and parse"}
        </button>
      </div>
    </section>
  );
}

function StatusPanel({
  health,
  healthError,
  uploadedFile,
  job,
}: {
  health: HealthResponse | null;
  healthError: string | null;
  uploadedFile: UploadedFileResponse | null;
  job: ProcessingJobResponse | null;
}) {
  const steps = [
    { label: "API connection", done: health?.status === "ok", detail: healthError ?? "FastAPI health check" },
    { label: "File stored", done: Boolean(uploadedFile), detail: uploadedFile?.original_filename ?? "Waiting" },
    { label: "Extraction job", done: Boolean(job), detail: job?.status ?? "Waiting" },
    {
      label: "Structured record",
      done: Boolean(uploadedFile && job?.status === "completed"),
      detail: "Schema-validated and persisted",
    },
  ];

  return (
    <section className="rounded-xl border border-cloud-200 bg-ink-950 p-5 text-white shadow-soft sm:p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-blue-200">Operations</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight">Pipeline status</h2>
        </div>
        <div className="grid h-10 w-10 place-items-center rounded-lg bg-white/10">
          <Workflow className="h-5 w-5" />
        </div>
      </div>

      <div className="mt-6 space-y-4">
        {steps.map((step, index) => (
          <div key={step.label} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div
                className={cx(
                  "grid h-8 w-8 place-items-center rounded-full border text-xs font-semibold",
                  step.done ? "border-mint-500 bg-mint-500 text-white" : "border-white/15 bg-white/5 text-white/60",
                )}
              >
                {step.done ? <CheckCircle2 className="h-4 w-4" /> : index + 1}
              </div>
              {index < steps.length - 1 ? <div className="h-8 w-px bg-white/10" /> : null}
            </div>
            <div>
              <p className="text-sm font-semibold">{step.label}</p>
              <p className="mt-1 text-xs text-white/55">{step.detail}</p>
            </div>
          </div>
        ))}
      </div>

      {job ? (
        <div className="mt-5 rounded-lg border border-white/10 bg-white/5 p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs text-white/50">Job ID</p>
              <p className="mt-1 truncate font-mono text-xs text-white/80">{job.job_id}</p>
            </div>
            <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-ink-950">{job.status}</span>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function ExtractionPreview({
  parsedDocument,
  extractedRecord,
}: {
  parsedDocument: ParsedDocumentResponse | null;
  extractedRecord: ExtractedRecordResponse | null;
}) {
  return (
    <section className="rounded-xl border border-cloud-200 bg-white p-5 shadow-soft sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-brand-700">Normalized source</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-ink-950">Extraction preview</h2>
        </div>
        <div className="flex items-center gap-2 rounded-lg border border-cloud-200 bg-cloud-50 px-3 py-2 text-xs font-semibold text-ink-500">
          <Search className="h-4 w-4" />
          Source-grounded
        </div>
      </div>

      {parsedDocument ? (
        <div className="mt-5 space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <InfoTile label="File type" value={parsedDocument.file_type.toUpperCase()} />
            <InfoTile label="Characters" value={String(parsedDocument.text.length)} />
            <InfoTile label="Tables" value={String(parsedDocument.tables.length)} />
          </div>
          <div className="rounded-lg border border-cloud-200 bg-cloud-50 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-ink-900">
              <FileJson2 className="h-4 w-4 text-brand-600" />
              Structured extraction
            </div>
            <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-white p-4 text-sm leading-6 text-ink-700 shadow-line">
              {extractedRecord
                ? JSON.stringify(extractedRecord.normalized_payload, null, 2)
                : parsedDocument.text || "No text extracted."}
            </pre>
          </div>
        </div>
      ) : (
        <EmptyState />
      )}
    </section>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-cloud-200 bg-cloud-50 p-4">
      <p className="text-xs font-medium text-ink-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-ink-950">{value}</p>
    </div>
  );
}

function ReportsPanel({
  uploadedFile,
  extractedRecord,
  records,
  validationErrors,
  generatedReports,
  onReportGenerated,
}: {
  uploadedFile: UploadedFileResponse | null;
  extractedRecord: ExtractedRecordResponse | null;
  records: ExtractedRecordResponse[];
  validationErrors: ValidationErrorResponse[];
  generatedReports: GeneratedReportResponse[];
  onReportGenerated: (report: GeneratedReportResponse) => void;
}) {
  const [reportError, setReportError] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [summaryReport, setSummaryReport] = useState<SummaryReportResponse | null>(null);
  const hasRecords = records.length > 0;
  const previewRecord = extractedRecord ?? records[0] ?? null;
  const previewAmount =
    typeof previewRecord?.normalized_payload.total_amount === "number"
      ? previewRecord.normalized_payload.total_amount
      : null;
  const previewCurrency =
    typeof previewRecord?.normalized_payload.currency === "string"
      ? previewRecord.normalized_payload.currency
      : "USD";
  const vendorTotals =
    summaryReport?.vendor_totals ??
    (previewRecord
      ? [
          {
            vendor_name: previewRecord.vendor_name ?? "Unknown vendor",
            total_amount: previewAmount ?? 0,
          },
        ]
      : []);
  const totalSpend = vendorTotals.reduce((total, vendor) => total + vendor.total_amount, 0);

  async function handleCreateReport(reportType: "summary" | "records", format: "json" | "csv") {
    setIsGenerating(true);
    setReportError(null);
    try {
      const report = await createReport(reportType, format);
      onReportGenerated(report);
      if (reportType === "summary" && format === "json") {
        const summary = await getSummaryReport(report.report_id);
        setSummaryReport(summary);
      }
    } catch (error) {
      setReportError(error instanceof Error ? error.message : "Report generation failed.");
    } finally {
      setIsGenerating(false);
    }
  }

  const rows = [
    {
      name: "Vendor spend summary",
      status: hasRecords ? `${records.length} records ready` : "Upload and extract first",
      icon: BarChart3,
    },
    {
      name: "Validation exceptions",
      status: hasRecords ? `${validationErrors.length} current findings` : "Waiting",
      icon: ShieldCheck,
    },
    {
      name: "Audit package",
      status: uploadedFile ? formatDate(uploadedFile.created_at) : `${generatedReports.length} reports`,
      icon: FileText,
    },
  ];

  return (
    <section className="rounded-xl border border-cloud-200 bg-white p-5 shadow-soft sm:p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-brand-700">Reports</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-ink-950">Executive outputs</h2>
        </div>
        <Clock3 className="h-5 w-5 text-ink-500" />
      </div>

      <div className="mt-5 space-y-3">
        {rows.map((row) => (
          <div key={row.name} className="flex items-center gap-3 rounded-lg border border-cloud-200 bg-cloud-50 p-3">
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-white text-ink-700 shadow-line">
              <row.icon className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-ink-900">{row.name}</p>
              <p className="text-xs text-ink-500">{row.status}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 grid gap-2 sm:grid-cols-2">
        <button
          className="rounded-lg bg-ink-950 px-3 py-2 text-sm font-semibold text-white transition hover:bg-ink-900 disabled:opacity-60"
          disabled={!hasRecords || isGenerating}
          onClick={() => void handleCreateReport("summary", "json")}
        >
          {isGenerating ? "Generating" : "Generate JSON"}
        </button>
        <button
          className="rounded-lg border border-cloud-200 bg-white px-3 py-2 text-sm font-semibold text-ink-900 transition hover:bg-cloud-50 disabled:opacity-60"
          disabled={!hasRecords || isGenerating}
          onClick={() => void handleCreateReport("records", "csv")}
        >
          Generate CSV
        </button>
      </div>

      <div className="mt-5 rounded-lg border border-cloud-200 bg-cloud-50 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-ink-900">Vendor spend summary</p>
            <p className="mt-1 text-xs text-ink-500">
              {hasRecords ? `${records.length} extracted records available` : "No records yet"}
            </p>
          </div>
          <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-brand-700 shadow-line">
            {summaryReport ? "Generated" : "Preview"}
          </span>
        </div>

        {hasRecords ? (
          <div className="mt-4 space-y-3">
            <div className="rounded-lg bg-white p-4 shadow-line">
              <p className="text-xs font-medium text-ink-500">Total vendor spend</p>
              <p className="mt-1 text-2xl font-semibold tracking-tight text-ink-950">
                {totalSpend.toLocaleString(undefined, {
                  style: "currency",
                  currency: previewCurrency,
                })}
              </p>
            </div>
            {vendorTotals.slice(0, 4).map((vendor) => (
              <div key={vendor.vendor_name} className="rounded-lg bg-white p-3 shadow-line">
                <div className="flex items-center justify-between gap-3">
                  <p className="truncate text-sm font-semibold text-ink-900">{vendor.vendor_name}</p>
                  <p className="text-sm font-semibold text-ink-700">
                    {vendor.total_amount.toLocaleString(undefined, {
                      style: "currency",
                      currency: previewCurrency,
                    })}
                  </p>
                </div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-cloud-100">
                  <div
                    className="h-full rounded-full bg-brand-600"
                    style={{
                      width: `${Math.max(
                        8,
                        totalSpend > 0 ? (vendor.total_amount / totalSpend) * 100 : 8,
                      )}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 rounded-lg bg-white p-4 text-sm leading-6 text-ink-500 shadow-line">
            Upload and extract at least one invoice, contract, CSV, email, or PDF before generating
            report outputs.
          </p>
        )}
      </div>

      {reportError ? (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {reportError}
        </div>
      ) : null}

      {extractedRecord ? (
        <div className="mt-5 rounded-lg border border-cloud-200 bg-cloud-50 p-4">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-ink-900">Validation result</p>
            <span
              className={cx(
                "rounded-full px-3 py-1 text-xs font-semibold",
                validationErrors.length === 0
                  ? "bg-mint-500/10 text-mint-600"
                  : "bg-amber-500/10 text-amber-700",
              )}
            >
              {validationErrors.length === 0 ? "Passed" : "Needs review"}
            </span>
          </div>
          <div className="mt-3 space-y-2">
            {validationErrors.length === 0 ? (
              <p className="text-sm leading-6 text-ink-500">
                Required fields, confidence, amounts, and source evidence checks passed.
              </p>
            ) : (
              validationErrors.slice(0, 3).map((error) => (
                <div key={error.validation_error_id} className="rounded-lg bg-white p-3 shadow-line">
                  <p className="text-xs font-semibold uppercase text-amber-700">{error.severity}</p>
                  <p className="mt-1 text-sm text-ink-700">{error.message}</p>
                </div>
              ))
            )}
          </div>
        </div>
      ) : null}

      {generatedReports.length > 0 ? (
        <div className="mt-5 space-y-2">
          <p className="text-sm font-semibold text-ink-900">Generated reports</p>
          {generatedReports.slice(0, 3).map((report) => (
            <a
              key={report.report_id}
              className="flex items-center justify-between rounded-lg border border-cloud-200 bg-cloud-50 px-3 py-2 text-sm transition hover:bg-white"
              href={getReportDownloadUrl(report.report_id)}
              rel="noreferrer"
              target="_blank"
            >
              <span className="font-medium text-ink-700">
                {report.report_type} / {String(report.parameters.format).toUpperCase()}
              </span>
              <span className="text-xs font-semibold text-brand-700">Download</span>
            </a>
          ))}
        </div>
      ) : null}

      <div className="mt-5 rounded-lg bg-gradient-to-br from-ink-950 to-brand-700 p-4 text-white">
        <p className="text-sm font-semibold">Next milestone</p>
        <p className="mt-2 text-sm leading-6 text-white/75">
          Phase 9 packages the API, dashboard, database, and runtime configuration for Docker-based
          deployment.
        </p>
      </div>
    </section>
  );
}

function ObservabilityPanel({
  auditLogs,
  extractionErrors,
  onRefresh,
}: {
  auditLogs: AuditLogResponse[];
  extractionErrors: ExtractionErrorResponse[];
  onRefresh: () => void;
}) {
  return (
    <section className="rounded-xl border border-cloud-200 bg-white p-5 shadow-soft sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-brand-700">Observability</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-ink-950">
            Pipeline control plane
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink-500">
            Request tracing, audit events, retry attempts, and extraction failures are surfaced for
            production-style operations.
          </p>
        </div>
        <button
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-cloud-200 bg-white px-3 py-2 text-sm font-semibold text-ink-900 transition hover:bg-cloud-50"
          onClick={onRefresh}
        >
          <Activity className="h-4 w-4" />
          Refresh
        </button>
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="rounded-lg border border-cloud-200 bg-cloud-50 p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-ink-900">Extraction errors</p>
            <span
              className={cx(
                "rounded-full px-3 py-1 text-xs font-semibold",
                extractionErrors.length === 0
                  ? "bg-mint-500/10 text-mint-600"
                  : "bg-red-500/10 text-red-700",
              )}
            >
              {extractionErrors.length}
            </span>
          </div>
          <div className="mt-4 space-y-2">
            {extractionErrors.length === 0 ? (
              <p className="rounded-lg bg-white p-4 text-sm leading-6 text-ink-500 shadow-line">
                No extraction errors recorded.
              </p>
            ) : (
              extractionErrors.slice(0, 4).map((error) => (
                <div key={error.error_id} className="rounded-lg bg-white p-3 shadow-line">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-ink-900">
                        {error.stage} / {error.error_type}
                      </p>
                      <p className="mt-1 line-clamp-2 text-xs leading-5 text-ink-500">
                        {error.message}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="rounded-lg border border-cloud-200 bg-cloud-50 p-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-ink-900">Recent audit events</p>
            <ShieldCheck className="h-4 w-4 text-mint-600" />
          </div>
          <div className="mt-4 overflow-hidden rounded-lg border border-cloud-200 bg-white">
            {auditLogs.length === 0 ? (
              <p className="p-4 text-sm leading-6 text-ink-500">No audit events yet.</p>
            ) : (
              auditLogs.slice(0, 6).map((event) => (
                <div
                  key={event.audit_log_id}
                  className="grid gap-2 border-b border-cloud-100 px-4 py-3 last:border-b-0 sm:grid-cols-[160px_1fr_120px]"
                >
                  <p className="truncate text-xs font-semibold text-brand-700">{event.action}</p>
                  <p className="truncate text-sm text-ink-700">
                    {event.entity_type}
                    {event.entity_id ? ` / ${event.entity_id}` : ""}
                  </p>
                  <p className="text-xs text-ink-500 sm:text-right">
                    {formatDate(event.created_at)}
                  </p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function EmptyState() {
  return (
    <div className="mt-5 grid place-items-center rounded-xl border border-dashed border-cloud-200 bg-cloud-50 px-6 py-14 text-center">
      <div className="grid h-12 w-12 place-items-center rounded-lg bg-white text-ink-700 shadow-line">
        <FileText className="h-6 w-6" />
      </div>
      <p className="mt-4 text-sm font-semibold text-ink-900">No parsed document yet</p>
      <p className="mt-1 max-w-sm text-sm leading-6 text-ink-500">
        Upload a supported document to see normalized text, metadata, tables, and parser-ready context.
      </p>
    </div>
  );
}
