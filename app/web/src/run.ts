import type { ArmKey, ArmMeta, Buff, Finding, Issue, Judgement, PromptSections, RunEvent, Usage } from "./api";

export interface Call {
  id: string; step: string; model: string; effort: string; schema: string; role?: string | null;
  system: string; user: string; round: number; startTs: number;
  status: "running" | "done" | "error"; seconds?: number; usage?: Usage | null; cost?: number;
  output?: any; error?: string;
}
export interface ReviewerRun {
  key: string; title: string; model: string; round: number; status: "running" | "done";
  findings?: Finding[] | null; verdict?: string; seconds?: number;
}
export interface Decision {
  round: number; blocking: Finding[]; advisory: Finding[]; dismissed: Finding[]; ran: Record<string, string>; publish: boolean;
}
export type Step =
  | { kind: "call"; id: string }
  | { kind: "buff"; round: number; buff: Buff; notes: string | null; ts: number }
  | { kind: "validators"; round: number; issues: Issue[]; ts: number }
  | { kind: "reviewers"; round: number }
  | { kind: "decision"; round: number }
  | { kind: "repair"; round: number; problems: string[]; ts: number }
  | { kind: "judge"; role: string; idx: number };

export interface JudgeRun { role: string; judgement: Judgement; penalty: number; mean: number; round: number }

export interface ArmState {
  key: ArmKey; meta?: ArmMeta; status: "idle" | "running" | "done" | "error";
  startTs?: number; seconds?: number; error?: string;
  calls: Record<string, Call>; steps: Step[];
  reviewers: ReviewerRun[]; decisions: Decision[]; judges: JudgeRun[];
  buff?: Buff; context?: PromptSections; lastValidators?: Issue[];
}

export interface RunState {
  status: "idle" | "running" | "done" | "error";
  arms: Partial<Record<ArmKey, ArmState>>;
  order: ArmKey[]; ts: number; error?: string; moment?: any; lang?: string;
}

export const emptyRun: RunState = { status: "idle", arms: {}, order: [], ts: 0 };

function arm(s: RunState, k: ArmKey): ArmState {
  return s.arms[k] ?? { key: k, status: "idle", calls: {}, steps: [], reviewers: [], decisions: [], judges: [] };
}

/** Fold one streamed event into the run state (immutable update of the touched arm). */
export function reduce(s: RunState, e: RunEvent): RunState {
  const ts = e.ts ?? s.ts;
  if (e.t === "run.start") return { ...emptyRun, status: "running", order: e.arms, moment: e.moment, lang: e.lang,
    arms: Object.fromEntries((e.arms as ArmKey[]).map((k) => [k, { ...arm(emptyRun, k), status: "running" }])) };
  if (e.t === "done") return { ...s, status: s.status === "error" ? "error" : "done", ts };
  if (e.t === "fatal") return { ...s, status: "error", error: e.error, ts };
  if (!e.arm) return { ...s, ts };

  const a: ArmState = { ...arm(s, e.arm) };
  const round = e.round ?? 0;
  switch (e.t) {
    case "arm.start": a.meta = e.meta; a.status = "running"; a.startTs = ts; break;
    case "context": a.context = { system: e.system, user: e.user, sections: e.sections }; break;
    case "llm.start": {
      if (e.step.startsWith("review.")) {
        // reviewer calls show inside their reviewer row, not as their own step
        a.calls = { ...a.calls, [e.id]: { id: e.id, step: e.step, model: e.model, effort: e.effort, schema: e.schema, role: e.role,
          system: e.system, user: e.user, round, startTs: ts, status: "running" } };
        break;
      }
      a.calls = { ...a.calls, [e.id]: { id: e.id, step: e.step, model: e.model, effort: e.effort, schema: e.schema, role: e.role,
        system: e.system, user: e.user, round, startTs: ts, status: "running" } };
      a.steps = [...a.steps, { kind: "call", id: e.id }];
      break;
    }
    case "llm.done": {
      const c = a.calls[e.id];
      if (c) a.calls = { ...a.calls, [e.id]: { ...c, status: "done", seconds: e.seconds, usage: e.usage, cost: e.cost, output: e.output } };
      break;
    }
    case "llm.error": {
      const c = a.calls[e.id];
      if (c) a.calls = { ...a.calls, [e.id]: { ...c, status: "error", seconds: e.seconds, error: e.error } };
      break;
    }
    case "buff": a.buff = e.buff; a.steps = [...a.steps, { kind: "buff", round, buff: e.buff, notes: e.notes, ts }]; break;
    case "validators": a.lastValidators = e.issues; a.steps = [...a.steps, { kind: "validators", round, issues: e.issues, ts }]; break;
    case "reviewer.start":
      if (!a.steps.some((st) => st.kind === "reviewers" && st.round === round)) a.steps = [...a.steps, { kind: "reviewers", round }];
      a.reviewers = [...a.reviewers, { key: e.key, title: e.title, model: e.model, round, status: "running" }];
      break;
    case "reviewer.done":
      a.reviewers = a.reviewers.map((r) => r.key === e.key && r.round === round
        ? { ...r, status: "done", findings: e.findings, verdict: e.verdict, seconds: e.seconds, model: e.model } : r);
      break;
    case "decision":
      a.decisions = [...a.decisions, { round, blocking: e.blocking, advisory: e.advisory, dismissed: e.dismissed, ran: e.ran, publish: e.publish }];
      a.steps = [...a.steps, { kind: "decision", round }];
      break;
    case "repair": a.steps = [...a.steps, { kind: "repair", round, problems: e.problems, ts }]; break;
    case "judge":
      a.judges = [...a.judges, { role: e.role, judgement: e.judgement, penalty: e.penalty, mean: e.mean, round }];
      a.steps = [...a.steps, { kind: "judge", role: e.role, idx: a.judges.length - 1 }];
      break;
    case "arm.done": a.status = "done"; a.seconds = e.seconds; if (e.buff) a.buff = e.buff; break;
    case "arm.error": a.status = "error"; a.seconds = e.seconds; a.error = e.error; break;
  }
  return { ...s, ts, arms: { ...s.arms, [e.arm]: a } };
}

export function totals(a: ArmState) {
  const calls = Object.values(a.calls);
  let cost = 0, input = 0, output = 0, cacheRead = 0, cacheWrite = 0;
  for (const c of calls) {
    cost += c.cost ?? 0;
    input += c.usage?.input ?? 0; output += c.usage?.output ?? 0;
    cacheRead += c.usage?.cache_read ?? 0; cacheWrite += c.usage?.cache_write ?? 0;
  }
  return { cost, input, output, cacheRead, cacheWrite, calls: calls.length };
}

/** The independent panel verdict, kept separate from C's in-loop judge. */
export function panelJudge(a: ArmState): JudgeRun | undefined {
  return [...a.judges].reverse().find((j) => j.role === "panel");
}

export const STEP_LABEL: Record<string, string> = {
  "A.english": "Write in English",
  "A.translate": "Translate (JIL button prompt)",
  "B.native": "Write natively (today's prompt)",
  "C.generate": "Write natively with locale pack",
  "C.repair": "Repair with routed fixes",
  judge: "Blind judge",
};
