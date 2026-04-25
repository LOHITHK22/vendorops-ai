export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

export type HealthResponse = {
  status: string;
  app_name: string;
  environment: string;
  timestamp: string;
};

export type UploadedFileResponse = {
  file_id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  sha256_hash: string;
  storage_path: string;
  created_at: string;
};

export type ProcessingJobResponse = {
  job_id: string;
  file_id: string;
  pipeline: string;
  status: "queued" | "running" | "completed" | "failed";
  created_at: string;
  updated_at: string;
  error_message?: string | null;
};

export type ParsedDocumentResponse = {
  source_path: string;
  file_type: string;
  text: string;
  metadata: Record<string, unknown>;
  pages: Array<{ page_number: number; text: string }>;
  tables: Array<{ name: string; columns: string[]; rows: Array<Record<string, unknown>> }>;
};

export type ExtractedRecordResponse = {
  record_id: string;
  file_id: string;
  job_id?: string | null;
  record_type: string;
  vendor_name?: string | null;
  external_reference?: string | null;
  confidence?: number | null;
  normalized_payload: Record<string, unknown>;
  raw_payload?: Record<string, unknown> | null;
  created_at: string;
};

export type ExtractionRunResponse = {
  job: ProcessingJobResponse;
  record: ExtractedRecordResponse;
  validation_errors: ValidationErrorResponse[];
};

export type ValidationErrorResponse = {
  validation_error_id: string;
  record_id?: string | null;
  job_id?: string | null;
  field_name?: string | null;
  error_type: string;
  message: string;
  severity: string;
  created_at: string;
};

export type GeneratedReportResponse = {
  report_id: string;
  report_type: string;
  status: string;
  parameters: Record<string, unknown>;
  storage_path?: string | null;
  created_at: string;
};

export type AuditLogResponse = {
  audit_log_id: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  details?: Record<string, unknown> | null;
  created_at: string;
};

export type ExtractionErrorResponse = {
  error_id: string;
  job_id?: string | null;
  file_id?: string | null;
  stage: string;
  error_type: string;
  message: string;
  retryable: boolean;
  attempt: number;
  details?: Record<string, unknown> | null;
  created_at: string;
};

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(payload.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  return parseJsonResponse<HealthResponse>(response);
}

export async function uploadFile(file: File): Promise<UploadedFileResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/v1/files`, {
    method: "POST",
    body: formData,
  });
  return parseJsonResponse<UploadedFileResponse>(response);
}

export async function createJob(fileId: string): Promise<ProcessingJobResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, pipeline: "document_extraction" }),
  });
  return parseJsonResponse<ProcessingJobResponse>(response);
}

export async function parseFile(fileId: string): Promise<ParsedDocumentResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/files/${fileId}/parsed`);
  return parseJsonResponse<ParsedDocumentResponse>(response);
}

export async function extractFile(fileId: string): Promise<ExtractionRunResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/files/${fileId}/extract`, {
    method: "POST",
  });
  return parseJsonResponse<ExtractionRunResponse>(response);
}

export async function createReport(
  reportType: "summary" | "records",
  format: "json" | "csv",
): Promise<GeneratedReportResponse> {
  const response = await fetch(`${API_BASE_URL}/v1/reports`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ report_type: reportType, format }),
  });
  return parseJsonResponse<GeneratedReportResponse>(response);
}

export async function getAuditLogs(limit = 8): Promise<AuditLogResponse[]> {
  const response = await fetch(`${API_BASE_URL}/v1/audit-logs?limit=${limit}`);
  return parseJsonResponse<AuditLogResponse[]>(response);
}

export async function getExtractionErrors(limit = 8): Promise<ExtractionErrorResponse[]> {
  const response = await fetch(`${API_BASE_URL}/v1/extraction-errors?limit=${limit}`);
  return parseJsonResponse<ExtractionErrorResponse[]>(response);
}

export function getReportDownloadUrl(reportId: string): string {
  return `${API_BASE_URL}/v1/reports/${reportId}/download`;
}
