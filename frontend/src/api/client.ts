import type { AuditResult, ComplianceRule } from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "https://audit-ai-lend.onrender.com";

async function fetchApi<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail)
    );
  }
  return res.json();
}

export async function runAudit(noteText: string): Promise<AuditResult> {
  return fetchApi<AuditResult>("/audit", {
    method: "POST",
    body: JSON.stringify({ note_text: noteText }),
  });
}

export async function getAudit(auditId: string): Promise<AuditResult> {
  return fetchApi<AuditResult>(`/audit/${auditId}`);
}

export async function listRules(): Promise<ComplianceRule[]> {
  return fetchApi<ComplianceRule[]>("/rules");
}
