import { useState, useEffect } from "react";
import { Shield } from "lucide-react";
import { NoteInput } from "./components/NoteInput";
import { AuditReport } from "./components/AuditReport";
import { RulesPanel } from "./components/RulesPanel";
import { runAudit, listRules } from "./api/client";
import type { AuditResult, ComplianceRule } from "./types";

export default function App() {
  const [noteText, setNoteText] = useState("");
  const [auditResult, setAuditResult] = useState<AuditResult | null>(null);
  const [rules, setRules] = useState<ComplianceRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [rulesLoading, setRulesLoading] = useState(true);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listRules()
      .then((r) => {
        setRules(r);
        setBackendOk(true);
      })
      .catch(() => {
        setRules([]);
        setBackendOk(false);
      })
      .finally(() => setRulesLoading(false));
  }, []);

  async function handleSubmit() {
    if (noteText.length < 50) return;
    setLoading(true);
    setError(null);
    try {
      const result = await runAudit(noteText);
      setAuditResult(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Audit failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[var(--bg)]">
      <header className="border-b border-[var(--border)] bg-[var(--bg-card)]">
        <div className="mx-auto max-w-4xl px-6 py-6">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg bg-[var(--accent)]/20">
              <Shield className="size-6 text-[var(--accent)]" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-[var(--text)]">
                AuditAI
              </h1>
              <p className="text-sm text-[var(--text-muted)]">
                Clinical note compliance auditor
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-6 py-8">
        <div className="space-y-8">
          <section>
            <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Clinical note
            </h2>
            <NoteInput
              value={noteText}
              onChange={setNoteText}
              onSubmit={handleSubmit}
              isLoading={loading}
            />
          </section>

          {backendOk === false && !loading && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-amber-400">
              Backend not connected. The API server may be starting up. Please wait 30 seconds and refresh.
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-red-400">
              {error}
            </div>
          )}

          <RulesPanel rules={rules} isLoading={rulesLoading} />

          {auditResult && (
            <section>
              <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                Audit result
              </h2>
              <AuditReport result={auditResult} />
            </section>
          )}
        </div>
      </main>

      <footer className="mt-16 border-t border-[var(--border)] py-6">
        <div className="mx-auto max-w-4xl px-6 text-center text-sm text-[var(--text-muted)]">
          AuditAI extracts structured fields from clinical notes and checks them
          against configurable compliance rules. Not a substitute for professional
          medical or legal advice.
        </div>
      </footer>
    </div>
  );
}
