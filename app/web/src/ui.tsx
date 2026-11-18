import { useEffect, useMemo, useState, type ReactNode } from "react";
import type { Buff, Section } from "./api";
import type { Call } from "./run";

export const SECTION_COLORS: Record<string, string> = {
  role: "var(--sec-role)", style: "var(--sec-style)", glossary: "var(--sec-glossary)",
  names: "var(--sec-names)", fewshot: "var(--sec-fewshot)", rules: "var(--sec-rules)", user: "var(--sec-user)",
};

export const tok = (chars: number) => Math.round(chars / 4);
export const fmtK = (n: number) => (n >= 1000 ? `${(n / 1000).toFixed(1)}k` : `${n}`);
export const usd = (n: number) => (n < 0.01 ? `$${n.toFixed(4)}` : `$${n.toFixed(3)}`);

export function Badge({ tone = "muted", children, title }: { tone?: string; children: ReactNode; title?: string }) {
  return <span className={`badge badge-${tone}`} title={title}>{children}</span>;
}

export function sevTone(sev: string) {
  if (sev === "critical" || sev === "error") return "bad";
  if (sev === "major") return "bad";
  if (sev.startsWith("warn") || sev === "minor") return "warn";
  return "muted";
}

export function Verdict({ v }: { v?: string }) {
  if (!v) return null;
  const tone = v === "approve" || v === "pass" ? "good" : v === "reject" ? "bad" : "warn";
  return <Badge tone={tone}>{v}</Badge>;
}

export function BuffCard({ buff, compact }: { buff: Buff; compact?: boolean }) {
  return (
    <div className={`buffcard ${compact ? "compact" : ""}`}>
      <div className="buffcard-top">
        <span className="buffcard-type">{buff.buff_type}</span>
        <span className="buffcard-title" title={`${buff.title.length} characters`}>{buff.title}</span>
      </div>
      <p className="buffcard-q">{buff.question}</p>
      <div className="buffcard-opts">
        {buff.options.map((o, i) => (
          <span key={i} className={`buffcard-opt ${buff.correct_index === i ? "correct" : ""}`}>{o}</span>
        ))}
      </div>
      {!compact && buff.reveal && <p className="buffcard-reveal">After it closes: {buff.reveal}</p>}
    </div>
  );
}

export function Collapse({ title, right, children, open: initial = false }: { title: ReactNode; right?: ReactNode; children: ReactNode; open?: boolean }) {
  const [open, setOpen] = useState(initial);
  return (
    <div className={`collapse ${open ? "open" : ""}`}>
      <button className="collapse-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="chev">{open ? "▾" : "▸"}</span>
        <span className="collapse-title">{title}</span>
        {right && <span className="collapse-right">{right}</span>}
      </button>
      {open && <div className="collapse-body">{children}</div>}
    </div>
  );
}

/** Stacked bar showing how much of a prompt each context section takes. */
export function CompositionBar({ sections, user }: { sections: Section[]; user?: string }) {
  const parts = [...sections.map((s) => ({ key: s.key, label: s.label, chars: s.chars })),
    ...(user ? [{ key: "user", label: "Match context (user message)", chars: user.length }] : [])];
  const total = parts.reduce((n, p) => n + p.chars, 0) || 1;
  return (
    <div>
      <div className="compbar">
        {parts.map((p) => (
          <span key={p.key} style={{ width: `${(p.chars / total) * 100}%`, background: SECTION_COLORS[p.key] }}
            title={`${p.label}: ${p.chars} chars (≈${tok(p.chars)} tokens)`} />
        ))}
      </div>
      <div className="complegend">
        {parts.map((p) => (
          <span key={p.key}><i style={{ background: SECTION_COLORS[p.key] }} />{p.label} <b>≈{fmtK(tok(p.chars))}</b></span>
        ))}
      </div>
    </div>
  );
}

/** The system prompt with each known section tinted, so you can see where every block lands. */
export function PromptText({ text, sections }: { text: string; sections?: Section[] }) {
  const segs = useMemo(() => {
    const marks: { start: number; end: number; key: string }[] = [];
    for (const s of sections ?? []) {
      if (!s.text || s.text.length < 8) continue;
      const i = text.indexOf(s.text);
      if (i >= 0) marks.push({ start: i, end: i + s.text.length, key: s.key });
    }
    marks.sort((a, b) => a.start - b.start);
    const out: { text: string; key?: string }[] = [];
    let pos = 0;
    for (const m of marks) {
      if (m.start < pos) continue;
      if (m.start > pos) out.push({ text: text.slice(pos, m.start) });
      out.push({ text: text.slice(m.start, m.end), key: m.key });
      pos = m.end;
    }
    if (pos < text.length) out.push({ text: text.slice(pos) });
    return out;
  }, [text, sections]);
  return (
    <pre className="prompt">
      {segs.map((s, i) => s.key
        ? <span key={i} className="seg" style={{ borderColor: SECTION_COLORS[s.key], background: `color-mix(in srgb, ${SECTION_COLORS[s.key]} 14%, transparent)` }}>{s.text}</span>
        : <span key={i}>{s.text}</span>)}
    </pre>
  );
}

export function Json({ value }: { value: unknown }) {
  return <pre className="json">{JSON.stringify(value, null, 2)}</pre>;
}

export function Drawer({ title, onClose, children }: { title: ReactNode; onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);
  return (
    <div className="drawer-wrap" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Details">
        <header className="drawer-head">
          <div className="drawer-title">{title}</div>
          <button className="btn ghost" onClick={onClose} aria-label="Close">✕</button>
        </header>
        <div className="drawer-body">{children}</div>
      </aside>
    </div>
  );
}

/** Everything one model call received and returned. */
export function CallDetail({ call, sections }: { call: Call; sections?: Section[] }) {
  const [tab, setTab] = useState<"system" | "user" | "output">("system");
  const isGen = call.step === "C.generate" || call.step === "C.repair";
  return (
    <div className="calldetail">
      <div className="kv">
        <span>Model</span><b>{call.model}{call.usage?.served_model && call.usage.served_model !== call.model ? ` (served ${call.usage.served_model})` : ""}</b>
        <span>Effort</span><b>{call.effort}</b>
        <span>Output schema</span><b>{call.schema}</b>
        <span>Time</span><b>{call.seconds ? `${call.seconds}s` : "running…"}</b>
        {call.usage && <>
          <span>Tokens</span>
          <b>{fmtK(call.usage.input)} in · {fmtK(call.usage.output)} out · {fmtK(call.usage.cache_write)} cache write · {fmtK(call.usage.cache_read)} cache read</b>
          <span>Cost</span><b>{usd(call.cost ?? 0)}</b>
        </>}
      </div>
      {isGen && sections && <div className="block"><h4>What went into the system prompt</h4><CompositionBar sections={sections} user={call.user} /></div>}
      <div className="tabs small">
        <button className={tab === "system" ? "on" : ""} onClick={() => setTab("system")}>System prompt <em>{fmtK(call.system.length)} chars</em></button>
        <button className={tab === "user" ? "on" : ""} onClick={() => setTab("user")}>User message <em>{fmtK(call.user.length)} chars</em></button>
        <button className={tab === "output" ? "on" : ""} onClick={() => setTab("output")}>Output</button>
      </div>
      {tab === "system" && <PromptText text={call.system} sections={isGen ? sections : undefined} />}
      {tab === "user" && <pre className="prompt">{call.user}</pre>}
      {tab === "output" && (call.error ? <p className="err">{call.error}</p> : call.output ? <Json value={call.output} /> : <p className="muted">Waiting for the model…</p>)}
    </div>
  );
}

export function Ticker({ from, running }: { from: number; running: boolean }) {
  const [now, setNow] = useState(performance.now());
  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setNow(performance.now()), 100);
    return () => clearInterval(id);
  }, [running]);
  return <>{((now - from) / 1000).toFixed(1)}s</>;
}
