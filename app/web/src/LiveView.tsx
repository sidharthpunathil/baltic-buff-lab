import { useState } from "react";
import type { ArmKey, ArmMeta, Finding } from "./api";
import { panelJudge, STEP_LABEL, totals, type ArmState, type Call, type RunState } from "./run";
import { Badge, BuffCard, CallDetail, Collapse, Drawer, fmtK, sevTone, Ticker, usd, Verdict } from "./ui";

const REVIEWER_LABEL: Record<string, string> = {
  grammar: "Grammar", terms: "Sport terms", names: "Names", native: "Native ear", facts: "Facts & card",
};

export function LiveView({ run, arms, runStartedAt }: { run: RunState; arms: ArmMeta[]; runStartedAt: number }) {
  const [open, setOpen] = useState<{ arm: ArmKey; call: string } | null>(null);
  if (run.status === "idle") {
    return (
      <div className="empty">
        <h2>Pick a match moment and press Run</h2>
        <p>Each column runs one method on the same moment, in the fan's language. Today's methods (A, B) race the new pipeline (C, D).
          Every model call streams in as it happens: click any step to see the exact prompt it received, what it returned, the tokens and the cost.</p>
        <div className="armlegend">
          {arms.map((a) => (
            <div key={a.key} className={`armlegend-item ${a.kind}`}>
              <b>{a.key}</b><div><strong>{a.name}</strong><p>{a.how}</p><small>{a.model}</small></div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  const cols = run.order.map((k) => run.arms[k]).filter(Boolean) as ArmState[];
  const call = open ? run.arms[open.arm]?.calls[open.call] : undefined;
  return (
    <>
      {run.error && <p className="err">{run.error}</p>}
      <Scoreboard cols={cols} />
      <div className="cols" style={{ gridTemplateColumns: `repeat(${cols.length}, minmax(300px, 1fr))` }}>
        {cols.map((a) => (
          <ArmColumn key={a.key} a={a} runStartedAt={runStartedAt} onOpen={(id) => setOpen({ arm: a.key, call: id })} />
        ))}
      </div>
      {open && call && (
        <Drawer title={<><b>{open.arm}</b> · {STEP_LABEL[call.step] ?? call.step} {call.round ? <Badge>round {call.round}</Badge> : null}</>}
          onClose={() => setOpen(null)}>
          <CallDetail call={call} sections={run.arms[open.arm]?.context?.sections} />
        </Drawer>
      )}
    </>
  );
}

function Scoreboard({ cols }: { cols: ArmState[] }) {
  if (!cols.some((a) => a.status === "done")) return null;
  return (
    <table className="scoreboard">
      <thead><tr><th>Method</th><th>Blind judge</th><th>Major + critical</th><th>MQM penalty</th><th>Mean score</th><th>Time</th><th>Calls</th><th>Cost</th></tr></thead>
      <tbody>
        {cols.map((a) => {
          const j = panelJudge(a); const t = totals(a);
          const majors = j ? j.judgement.errors.filter((e) => e.severity !== "minor").length : undefined;
          return (
            <tr key={a.key} className={a.meta?.kind}>
              <td><b>{a.key}</b> {a.meta?.name}</td>
              <td>{j ? <Verdict v={j.judgement.verdict} /> : a.status === "running" ? "…" : "–"}</td>
              <td>{majors ?? "–"}</td>
              <td>{j ? j.penalty : "–"}</td>
              <td>{j ? j.mean.toFixed(1) : "–"}</td>
              <td>{a.seconds ? `${a.seconds}s` : "…"}</td>
              <td>{t.calls}</td>
              <td>{usd(t.cost)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

function ArmColumn({ a, onOpen, runStartedAt }: { a: ArmState; onOpen: (id: string) => void; runStartedAt: number }) {
  const t = totals(a);
  const j = panelJudge(a);
  return (
    <section className={`col ${a.meta?.kind ?? ""}`}>
      <header className="col-head">
        <div className="col-key">{a.key}</div>
        <div>
          <h3>{a.meta?.name ?? a.key}</h3>
          <p>{a.meta?.how}</p>
        </div>
        <div className="col-status">
          {a.status === "running" && a.startTs !== undefined && <span className="live"><i />{<Ticker from={runStartedAt + a.startTs * 1000} running />}</span>}
          {a.status === "done" && <Badge tone="good">{a.seconds}s</Badge>}
          {a.status === "error" && <Badge tone="bad">failed</Badge>}
        </div>
      </header>

      {a.buff ? (
        <div className="col-result">
          <BuffCard buff={a.buff} />
          <p className="gloss"><span>English meaning</span>{a.buff.english_gloss}</p>
        </div>
      ) : a.status === "running" ? <div className="skeleton">Writing the buff…</div> : null}
      {a.error && <p className="err">{a.error}</p>}

      {j && (
        <div className={`judgebox ${j.judgement.verdict}`}>
          <div className="judgebox-head">
            <span>Blind judge</span><Verdict v={j.judgement.verdict} />
            <span className="muted">penalty {j.penalty} · mean {j.mean.toFixed(1)}/5</span>
          </div>
          <div className="scores">
            {(["grammar", "naturalness", "terminology", "faithfulness", "engagement"] as const).map((k) => (
              <span key={k} title={k}><em>{k}</em><b className={`s${j.judgement[k]}`}>{j.judgement[k]}</b></span>
            ))}
          </div>
          {j.judgement.errors.length > 0 && (
            <ul className="errlist">
              {j.judgement.errors.map((e, i) => (
                <li key={i}><Badge tone={sevTone(e.severity)}>{e.severity}</Badge> <code>{e.span}</code> <span className="muted">{e.category}</span>
                  <p>{e.explanation}</p>{e.suggested_fix && <p className="fix">→ {e.suggested_fix}</p>}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="timeline">
        <h4>What happened, step by step</h4>
        {a.steps.map((st, i) => <StepRow key={i} st={st} a={a} onOpen={onOpen} runStartedAt={runStartedAt} />)}
      </div>

      <footer className="col-foot">
        <span>{t.calls} model calls</span>
        <span>{fmtK(t.input + t.cacheWrite + t.cacheRead)} in / {fmtK(t.output)} out</span>
        <span>{usd(t.cost)}</span>
      </footer>
    </section>
  );
}

function CallRow({ c, onOpen, runStartedAt, label }: { c: Call; onOpen: (id: string) => void; runStartedAt: number; label?: string }) {
  return (
    <button className={`step call ${c.status}`} onClick={() => onOpen(c.id)}>
      <span className="dot" />
      <span className="step-name">{label ?? STEP_LABEL[c.step] ?? c.step}{c.role === "panel" ? " (independent)" : c.step === "judge" ? " (in-loop)" : ""}</span>
      <span className="step-meta">
        {c.model.replace("claude-", "")} · {fmtK(c.system.length + c.user.length)} chars in
        {c.status === "running" ? <> · <Ticker from={runStartedAt + c.startTs * 1000} running /></> : c.seconds ? ` · ${c.seconds}s` : ""}
        {c.cost ? ` · ${usd(c.cost)}` : ""}
      </span>
      <span className="step-open">inspect ›</span>
    </button>
  );
}

function StepRow({ st, a, onOpen, runStartedAt }: { st: ArmState["steps"][number]; a: ArmState; onOpen: (id: string) => void; runStartedAt: number }) {
  switch (st.kind) {
    case "call": {
      const c = a.calls[st.id];
      return c ? <CallRow c={c} onOpen={onOpen} runStartedAt={runStartedAt} /> : null;
    }
    case "buff":
      if (!st.notes && st.round === 0) return null;
      return (
        <Collapse title={<>Draft {st.round > 0 ? `after repair ${st.round}` : ""}</>} right={<span className="muted small">{st.buff.question.slice(0, 40)}…</span>}>
          <BuffCard buff={st.buff} compact />
          {st.notes && <><h5>The model's case notes</h5><p className="notes">{st.notes}</p></>}
        </Collapse>
      );
    case "validators": {
      const errs = st.issues.filter((i) => i.severity === "error").length;
      return (
        <Collapse title={<>Automatic checks</>} right={st.issues.length === 0 ? <Badge tone="good">clean</Badge>
          : <><Badge tone={errs ? "bad" : "warn"}>{errs} errors</Badge> <Badge tone="warn">{st.issues.length - errs} warnings</Badge></>}>
          {st.issues.length === 0 ? <p className="muted">No spelling, alphabet, glossary, length or locale-rule problems.</p> :
            <ul className="issues">{st.issues.map((i, k) => <li key={k}><Badge tone={sevTone(i.severity)}>{i.severity}</Badge> <code>{i.code}</code> {i.message}</li>)}</ul>}
        </Collapse>
      );
    }
    case "reviewers": {
      const rs = a.reviewers.filter((r) => r.round === st.round);
      return (
        <div className="reviewers">
          <div className="reviewers-head">Five specialist reviewers, in parallel {st.round ? `(round ${st.round})` : ""}</div>
          {rs.map((r) => {
            const call = Object.values(a.calls).find((c) => c.step === `review.${r.key}` && c.round === st.round);
            const n = r.findings?.length ?? 0;
            return (
              <button key={r.key} className={`reviewer ${r.status}`} onClick={() => call && onOpen(call.id)}>
                <span className="dot" />
                <b>{REVIEWER_LABEL[r.key] ?? r.key}</b>
                <span className="muted">{r.status === "running" ? "reading…" : `${r.seconds}s`}</span>
                {r.status === "done" && (n === 0 ? <Badge tone="good">pass</Badge> : <Badge tone="warn">{n} finding{n > 1 ? "s" : ""}</Badge>)}
              </button>
            );
          })}
        </div>
      );
    }
    case "decision": {
      const d = a.decisions.find((x) => x.round === st.round);
      if (!d) return null;
      return (
        <Collapse title={<>Orchestrator decision</>} open={!d.publish}
          right={d.publish ? <Badge tone="good">publish</Badge> : <Badge tone="bad">{d.blocking.length} blocking → repair</Badge>}>
          <FindingList title="Blocking" items={d.blocking} tone="bad" />
          <FindingList title="Advisory (shown to the operator)" items={d.advisory} tone="warn" />
          <FindingList title="Dismissed by rule" items={d.dismissed} tone="muted" />
          {d.blocking.length + d.advisory.length + d.dismissed.length === 0 && <p className="muted">Every reviewer passed the card.</p>}
        </Collapse>
      );
    }
    case "repair":
      return (
        <Collapse title={<>Repair brief sent back to the writer (round {st.round})</>} open>
          <ul className="issues">{st.problems.map((p, k) => <li key={k}>{p}</li>)}</ul>
        </Collapse>
      );
    case "judge":
      return null;
  }
}

function FindingList({ title, items, tone }: { title: string; items: Finding[]; tone: string }) {
  if (!items.length) return null;
  return (
    <div className="findings">
      <h5>{title}</h5>
      <ul>
        {items.map((f, i) => (
          <li key={i}>
            <Badge tone={tone}>{f.reviewer}</Badge> <Badge tone={sevTone(f.severity)}>{f.severity}</Badge>
            <span className="muted"> confidence {Math.round(f.confidence * 100)}%</span>
            <div><code>{f.span}</code> → <code>{f.fix}</code></div>
            <p>{f.problem}</p>
            {f.why && <p className="why">Dismissed: {f.why}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}
