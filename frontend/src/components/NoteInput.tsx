import { Loader2, FileText } from "lucide-react";

const SAMPLE_NOTE = `Patient is a 67-year-old male presenting with chest pain and shortness of breath. History of hypertension and type 2 diabetes. Current medications include metformin 1000mg, lisinopril 10mg, and oxycodone 5mg PRN. Vitals: BP 158/92, HR 88, O2 sat 96%. EKG showed ST changes. Admitted for observation and cardiac workup.`;

interface NoteInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export function NoteInput({ value, onChange, onSubmit, isLoading }: NoteInputProps) {
  const isValid = value.length >= 50;

  return (
    <div className="space-y-4">
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Paste or type a clinical note (minimum 50 characters)..."
          className="min-h-[200px] w-full resize-y rounded-lg border border-[var(--border)] bg-[var(--bg-card)] px-4 py-3 text-[var(--text)] placeholder:text-[var(--text-muted)] focus:border-[var(--accent)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
          disabled={isLoading}
          spellCheck={false}
        />
        <div className="mt-2 flex items-center justify-between">
          <span className="text-sm text-[var(--text-muted)]">
            {value.length} characters
          </span>
          <button
            type="button"
            onClick={() => onChange(SAMPLE_NOTE)}
            className="inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm text-[var(--text-muted)] hover:bg-[var(--bg-elevated)] hover:text-[var(--text)]"
          >
            <FileText className="size-4" />
            Sample note
          </button>
        </div>
      </div>
      <button
        type="button"
        onClick={onSubmit}
        disabled={!isValid || isLoading}
        className="inline-flex items-center gap-2 rounded-lg bg-[var(--accent)] px-6 py-3 font-medium text-[#0a0c10] transition hover:bg-[var(--accent-dim)] disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isLoading ? (
          <>
            <Loader2 className="size-5 animate-spin" />
            Running audit...
          </>
        ) : (
          "Run audit"
        )}
      </button>
    </div>
  );
}
