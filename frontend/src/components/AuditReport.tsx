import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileOutput,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import type { AuditResult as AuditResultType } from "../types";
import { RiskBadge } from "./RiskBadge";

const SCORE_COLORS: Record<string, string> = {
  LOW: "stroke-emerald-500",
  MEDIUM: "stroke-amber-500",
  HIGH: "stroke-orange-500",
  CRITICAL: "stroke-red-500",
};

interface AuditReportProps {
  result: AuditResultType;
}

function ScoreRing({ score, level }: { score: number; level: string }) {
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (score / 100) * circumference;
  const colorClass = SCORE_COLORS[level] ?? "stroke-[var(--accent)]";

  return (
    <div className="relative inline-flex">
      <svg className="size-28 -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-[var(--bg-elevated)]"
        />
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className={`transition-all duration-700 ${colorClass}`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold">{score}</span>
        <span className="text-xs text-[var(--text-muted)]">Risk</span>
      </div>
    </div>
  );
}

function FieldCard({
  label,
  value,
}: {
  label: string;
  value: string | number | string[] | null;
}) {
  const display =
    value === null || value === undefined
      ? "Not documented"
      : Array.isArray(value)
        ? value.length === 0
          ? "None"
          : value.join(", ")
        : String(value);

  return (
    <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] p-3">
      <div className="text-xs font-medium text-[var(--text-muted)]">{label}</div>
      <div className="mt-1 text-sm text-[var(--text)]">{display}</div>
    </div>
  );
}

export function AuditReport({ result }: AuditReportProps) {
  const f = result.extracted_fields;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start gap-6">
        <div className="flex flex-col items-center gap-3">
          <ScoreRing score={result.risk_score} level={result.risk_level} />
          <RiskBadge level={result.risk_level} />
        </div>
        <div className="flex flex-1 flex-col gap-2">
          <div className="flex items-center gap-2 text-[var(--text-muted)]">
            <Clock className="size-4" />
            <span className="text-sm">
              Processed in {result.processing_time_ms}ms
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            <span className="rounded-md bg-[var(--bg-elevated)] px-2 py-1 text-xs">
              {result.total_violations} violations
            </span>
            {result.critical_count > 0 && (
              <span className="rounded-md bg-red-500/20 px-2 py-1 text-xs text-red-400">
                {result.critical_count} critical
              </span>
            )}
            {result.high_count > 0 && (
              <span className="rounded-md bg-orange-500/20 px-2 py-1 text-xs text-orange-400">
                {result.high_count} high
              </span>
            )}
          </div>
        </div>
      </div>

      <div>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[var(--text)]">
          <FileOutput className="size-4" />
          Extracted fields
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <FieldCard label="Patient age" value={f.patient_age} />
          <FieldCard label="Visit type" value={f.visit_type} />
          <FieldCard label="Provider specialty" value={f.provider_specialty} />
          <FieldCard label="Diagnosis codes (ICD-10)" value={f.diagnosis_codes} />
          <FieldCard label="Procedure codes (CPT)" value={f.procedure_codes} />
          <FieldCard label="Medications" value={f.medications_mentioned} />
          <FieldCard
            label="Extraction confidence"
            value={
              f.extraction_confidence != null
                ? `${Math.round(f.extraction_confidence * 100)}%`
                : null
            }
          />
          {f.risk_flags_raw.length > 0 && (
            <FieldCard label="LLM risk flags" value={f.risk_flags_raw} />
          )}
        </div>
      </div>

      {result.violations.length > 0 && (
        <div>
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[var(--text)]">
            <AlertTriangle className="size-4" />
            Violations ({result.violations.length})
          </h3>
          <div className="space-y-2">
            {result.violations.map((v) => (
              <ViolationCard key={`${v.rule_id}-${v.field_checked}`} v={v} />
            ))}
          </div>
        </div>
      )}

      {result.violations.length === 0 && (
        <div className="flex items-center gap-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-4">
          <CheckCircle2 className="size-5 shrink-0 text-emerald-500" />
          <div>
            <div className="font-medium text-emerald-400">No violations</div>
            <div className="text-sm text-[var(--text-muted)]">
              This note passed all active compliance rules.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ViolationCard({
  v,
}: {
  v: AuditResultType["violations"][number];
}) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div
      className="rounded-lg border border-[var(--border)] bg-[var(--bg-card)] overflow-hidden"
    >
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-3 p-4 text-left hover:bg-[var(--bg-elevated)]"
      >
        {expanded ? (
          <ChevronDown className="size-4 shrink-0 text-[var(--text-muted)]" />
        ) : (
          <ChevronRight className="size-4 shrink-0 text-[var(--text-muted)]" />
        )}
        <RiskBadge level={v.severity} />
        <span className="text-sm font-medium">{v.rule_name}</span>
        <span className="text-xs text-[var(--text-muted)]">{v.category}</span>
      </button>
      {expanded && (
        <div className="border-t border-[var(--border)] p-4 pt-3">
          <div className="mb-2 text-xs text-[var(--text-muted)]">
            Field: {v.field_checked}
            {v.expected != null && ` | Expected: ${v.expected}`}
            {v.actual != null && ` | Actual: ${v.actual}`}
          </div>
          <div className="text-sm text-[var(--text)]">{v.recommendation}</div>
        </div>
      )}
    </div>
  );
}

