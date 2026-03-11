export interface ExtractedFields {
  patient_age: number | null;
  diagnosis_codes: string[];
  procedure_codes: string[];
  visit_type: string | null;
  provider_specialty: string | null;
  medications_mentioned: string[];
  risk_flags_raw: string[];
  extraction_confidence: number;
}

export interface RuleViolation {
  rule_id: number;
  rule_name: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  category: string;
  field_checked: string;
  expected: string | null;
  actual: string | null;
  recommendation: string;
}

export interface AuditResult {
  audit_id: string;
  risk_score: number;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  extracted_fields: ExtractedFields;
  violations: RuleViolation[];
  processing_time_ms: number;
  total_violations: number;
  critical_count: number;
  high_count: number;
}

export interface ComplianceRule {
  id: number;
  name: string;
  description: string;
  field: string;
  operator: string;
  value: string | null;
  severity: string;
  category: string;
  is_active: boolean;
}
