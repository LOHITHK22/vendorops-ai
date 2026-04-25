import {
  Activity,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock3,
  Database,
  FileJson2,
  FileText,
  Gauge,
  Layers3,
  Loader2,
  LockKeyhole,
  Search,
  Server,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  Workflow,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  API_BASE_URL,
  type HealthResponse,
  type ParsedDocumentResponse,
  type ProcessingJobResponse,
  type UploadedFileResponse,
  createJob,
  getHealth,
  parseFile,
  uploadFile,
} from "./api";

type UploadState = "idle" | "uploading" | "uploaded" | "error";
type IconComponent = typeof FileText;

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
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedFile, setUploadedFile] = useState<UploadedFileResponse | null>(null);
  const [job, setJob] = useState<ProcessingJobResponse | null>(null);
  const [parsedDocument, setParsedDocument] = useState<ParsedDocumentResponse | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch((error: Error) => setHealthError(error.message));
  }, []);

  const metrics = useMemo(
    () => [
      {
        label: "Documents processed",
        value: uploadedFile ? "1" : "0",
        change: uploadedFile ? "Ready for extraction" : "Awaiting upload",
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
        value: parsedDocument ? "Live" : "Idle",
        change: parsedDocument ? `${parsedDocument.file_type.toUpperCase()} normalized` : "Parser standby",
        icon: Gauge,
      },
      {
        label: "API status",
        value: health?.status === "ok" ? "Online" : "Check",
        change: health ? health.environment : healthError ?? "Connecting",
        icon: Server,
      },
    ],
    [health, healthError, job, parsedDocument, uploadedFile],
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

    try {
      const uploaded = await uploadFile(selectedFile);
      setUploadedFile(uploaded);
      const [newJob, parsed] = await Promise.all([
        createJob(uploaded.file_id),
        parseFile(uploaded.file_id),
      ]);
      setJob(newJob);
      setParsedDocument(parsed);
      setUploadState("uploaded");
    } catch (error) {
      setUploadState("error");
      setFormError(error instanceof Error ? error.message : "Upload failed.");
    }
  }

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,#eff6ff_0,#f8fafc_34%,#ffffff_72%)] text-ink-900">
      <div className="mx-auto flex min-h-screen w-full max-w-[1500px] flex-col lg:flex-row">
        <Sidebar />
        <main className="flex-1 px-4 py-4 sm:px-6 lg:px-8">
          <TopBar health={health} healthError={healthError} />

          <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {metrics.map((metric) => (
              <MetricCard key={metric.label} {...metric} />
            ))}
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(360px,0.9fr)]">
            <UploadPanel
              selectedFile={selectedFile}
              uploadState={uploadState}
              formError={formError}
              onFileSelect={setSelectedFile}
              onUpload={handleUpload}
            />
            <StatusPanel health={health} healthError={healthError} uploadedFile={uploadedFile} job={job} />
          </section>

          <section className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
            <ExtractionPreview parsedDocument={parsedDocument} />
            <ReportsPanel uploadedFile={uploadedFile} parsedDocument={parsedDocument} />
          </section>
        </main>
      </div>
    </div>
  );
}

function Sidebar() {
  const navItems = [
    { label: "Command Center", icon: Layers3, active: true },
    { label: "Ingestion", icon: UploadCloud },
    { label: "Jobs", icon: Workflow },
    { label: "Records", icon: Database },
    { label: "Reports", icon: BarChart3 },
    { label: "Audit", icon: ShieldCheck },
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
            className={cx(
              "group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition",
              item.active
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
          PDF · CSV · TXT · EML
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
    { label: "Job created", done: Boolean(job), detail: job?.status ?? "Waiting" },
    { label: "Ready for extraction", done: Boolean(uploadedFile && job), detail: "Phase 4 connects LLM output" },
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

function ExtractionPreview({ parsedDocument }: { parsedDocument: ParsedDocumentResponse | null }) {
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
              Parsed text sample
            </div>
            <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-white p-4 text-sm leading-6 text-ink-700 shadow-line">
              {parsedDocument.text || "No text extracted."}
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
  parsedDocument,
}: {
  uploadedFile: UploadedFileResponse | null;
  parsedDocument: ParsedDocumentResponse | null;
}) {
  const rows = [
    {
      name: "Vendor spend summary",
      status: uploadedFile ? "Ready soon" : "Waiting",
      icon: BarChart3,
    },
    {
      name: "Validation exceptions",
      status: parsedDocument ? "Parser data ready" : "Waiting",
      icon: ShieldCheck,
    },
    {
      name: "Audit package",
      status: uploadedFile ? formatDate(uploadedFile.created_at) : "Waiting",
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

      <div className="mt-5 rounded-lg bg-gradient-to-br from-ink-950 to-brand-700 p-4 text-white">
        <p className="text-sm font-semibold">Next milestone</p>
        <p className="mt-2 text-sm leading-6 text-white/75">
          Phase 4 adds structured LLM extraction so these report modules can shift from preview state
          into real AI-enriched outputs.
        </p>
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
