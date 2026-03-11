"""Prometheus metrics for AuditAI."""

from prometheus_client import Counter, Histogram

# Audit requests by risk level
audit_requests_total = Counter(
    "audit_requests_total",
    "Total audit requests completed",
    ["risk_level"],
)

# LLM extraction latency
extraction_latency_seconds = Histogram(
    "extraction_latency_seconds",
    "LLM extraction latency in seconds",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

# Rule violations by severity and category
rule_violations_total = Counter(
    "rule_violations_total",
    "Total rule violations detected",
    ["severity", "category"],
)

# Full audit processing time
audit_processing_seconds = Histogram(
    "audit_processing_seconds",
    "End-to-end audit processing time in seconds",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)
