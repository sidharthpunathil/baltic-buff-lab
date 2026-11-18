export type ArmKey = "A" | "B" | "C" | "D";
export type Lang = "lt" | "lv" | "et";

export interface Moment { id: string; buff_type: string; state: string; text: string }
export interface Entity { name: string; kind: string; qid?: string }
export interface MatchEvent {
  id: string; sport: string; competition: string; home: string; away: string;
  moments: Moment[]; facts: string[]; entities: Entity[];
}
export interface ArmMeta { key: ArmKey; name: string; kind: "old" | "new"; how: string; model: string }
export interface Meta {
  events: MatchEvent[]; arms: ArmMeta[]; langs: Record<Lang, string>;
  settings: Record<string, string | number>;
}

export interface Buff {
  buff_type: string; title: string; question: string; options: string[];
  correct_index: number | null; reveal: string; english_gloss: string;
}
export interface Issue { code: string; severity: string; message: string }
export interface Finding { reviewer?: string; severity: string; span: string; problem: string; fix: string; confidence: number; why?: string }
export interface MQMError { category: string; severity: string; span: string; explanation: string; suggested_fix: string }
export interface Judgement {
  errors: MQMError[]; grammar: number; naturalness: number; terminology: number; faithfulness: number;
  engagement: number; verdict: string; native_rewrite: Buff | null;
}
export interface Usage { input: number; output: number; cache_write: number; cache_read: number; served_model?: string }
export interface Section { key: string; label: string; text: string; chars: number }
export interface PromptSections { system: string; user: string; sections: Section[] }

export interface FormsTable {
  lemma: string; gender: string; declines: boolean; usage_note: string;
  forms: { case: string; singular: string; short: string }[];
}
export interface ExploreEntity {
  name: string; kind: string; qid: string; labels: Record<string, string | null>; aliases: string[];
  label: string; label_source: string; forms: FormsTable; forms_press: FormsTable; tezaurs: boolean;
  press: { lemma: string; evidence: string; sources: string[]; cases?: Record<string, string>; substitute?: Record<string, string> } | null;
}
export interface GlossaryRow { en: string; term: string; avoid?: string[]; pos?: string; sport?: string; note?: string; source?: string; verified?: boolean }
export interface Reviewer { key: string; title: string; model: string; brief: string; needs: string[]; system: string; chars: number }
export interface Explore {
  entities: ExploreEntity[];
  pack: { style: string; facts: Record<string, unknown>; glossary: GlossaryRow[]; glossary_total: number;
          fewshot: Record<string, unknown>[]; fewshot_picked: number };
  prompt_d: PromptSections; prompt_c: PromptSections;
  prompt_a: { english_system: string; translate_system: string; user: string };
  prompt_b: { system: string; user: string; source: string };
  schema: unknown;
  reviewers: Reviewer[];
  validator_rules: { code: string; severity: string; what: string }[];
  orchestrator_rules: string[];
  settings: { max_repairs: number };
}

export async function getJSON<T>(url: string): Promise<T> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export async function postJSON<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
}

export type RunEvent = { t: string; arm?: ArmKey; round?: number; ts?: number; [k: string]: any };

/** POST /api/run and hand each NDJSON line to onEvent as it arrives. */
export async function streamRun(body: unknown, onEvent: (e: RunEvent) => void, signal: AbortSignal) {
  const r = await fetch("/api/run", {
    method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body), signal,
  });
  if (!r.ok || !r.body) throw new Error(`${r.status} ${await r.text()}`);
  const reader = r.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let nl;
    while ((nl = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, nl).trim();
      buf = buf.slice(nl + 1);
      if (line) onEvent(JSON.parse(line));
    }
  }
}
