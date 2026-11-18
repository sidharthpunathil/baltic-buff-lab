import { useEffect, useMemo, useState } from "react";
import { postJSON, type Buff, type Explore, type ExploreEntity, type Issue, type Lang, type MatchEvent } from "./api";
import type { RunState } from "./run";
import { Badge, BuffCard, CompositionBar, fmtK, Json, PromptText, sevTone, tok } from "./ui";

const STAGES = [
  { n: 1, key: "names", phase: "Before kickoff", title: "Real names",
    blurb: "Every team and player is looked up on Wikidata, which stores how each language's editors spell them." },
  { n: 2, key: "forms", phase: "Before kickoff", title: "Every grammatical form",
    blurb: "A table of every case form per name: drafted by Claude, Tēzaurs for Latvian players, then corrected from native sports press." },
  { n: 3, key: "pack", phase: "Per language", title: "Local knowledge in the prompt",
    blurb: "A style sheet, a sport glossary and example buffs per language, editable as plain files." },
  { n: 4, key: "prompt", phase: "Per live moment", title: "Written, not translated",
    blurb: "Everything above is assembled into one prompt. Claude writes in the fan's language and adds an English meaning." },
  { n: 5, key: "checks", phase: "Per live moment", title: "Automatic checks",
    blurb: "Spelling, accents, wrong Baltic alphabet, banned calques, locale rules and card length, in milliseconds." },
  { n: 6, key: "review", phase: "Per live moment (D)", title: "Five specialist reviewers",
    blurb: "Grammar, sport terms, names, native ear and facts check in parallel; a plain-code orchestrator decides." },
] as const;

type StageKey = (typeof STAGES)[number]["key"];

export function ExploreView({ data, event, lang, run }: { data: Explore | null; event: MatchEvent; lang: Lang; run: RunState }) {
  const [stage, setStage] = useState<StageKey>("prompt");
  return (
    <div className="explore">
      <div className="stages">
        {STAGES.map((s) => (
          <button key={s.key} className={`stage ${stage === s.key ? "on" : ""}`} onClick={() => setStage(s.key)}>
            <span className="stage-phase">{s.phase}</span>
            <h3>{s.n}. {s.title}</h3>
            <p>{s.blurb}</p>
          </button>
        ))}
      </div>
      <div className="stage-detail">
        {!data ? <p className="muted">Loading the real data for {event.home} vs {event.away}…</p> : <>
          {stage === "names" && <Names data={data} lang={lang} />}
          {stage === "forms" && <Forms data={data} lang={lang} />}
          {stage === "pack" && <Pack data={data} event={event} />}
          {stage === "prompt" && <Prompt data={data} run={run} />}
          {stage === "checks" && <Checks data={data} event={event} lang={lang} run={run} />}
          {stage === "review" && <Review data={data} run={run} />}
        </>}
      </div>
    </div>
  );
}

function Intro({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="intro"><h2>{title}</h2><div>{children}</div></div>;
}

// ---------------------------------------------------------------- 1. names
function Names({ data, lang }: { data: Explore; lang: Lang }) {
  const cols = ["en", "mul", "lt", "lv", "et"];
  return (
    <>
      <Intro title="1. Real names from Wikidata">
        <p><code>bbl/entities.py</code> calls Wikidata's <code>wbgetentities</code> for each QID and caches the labels in <code>data/cache/wd_&lt;qid&gt;.json</code>.
          The label for <b>{lang}</b> falls back to the shared <code>mul</code> label, then English. The highlighted cell is the one this match uses.</p>
      </Intro>
      <table className="grid">
        <thead><tr><th>Entity</th>{cols.map((c) => <th key={c} className={c === lang ? "hl" : ""}>{c}</th>)}<th>Used</th></tr></thead>
        <tbody>
          {data.entities.map((e) => (
            <tr key={e.name}>
              <td><b>{e.name}</b><div className="muted small">{e.kind} · <a href={`https://www.wikidata.org/wiki/${e.qid}`} target="_blank" rel="noreferrer">{e.qid}</a></div></td>
              {cols.map((c) => {
                const used = e.label_source === `wikidata:${c}` || (c === "en" && e.label_source === "fallback:en");
                return <td key={c} className={used ? "used" : e.labels[c] ? "" : "missing"}>{e.labels[c] ?? "—"}</td>;
              })}
              <td><Badge tone={e.label_source.startsWith("wikidata:" + lang) ? "good" : "warn"}>{e.label_source}</Badge></td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="note">Player labels are often missing in lt and et since Wikidata moved to a shared <code>mul</code> label. That's why stage 2 builds forms on top, and stage 2's press check matters most for players.</p>
    </>
  );
}

// ---------------------------------------------------------------- 2. forms
function Forms({ data, lang }: { data: Explore; lang: Lang }) {
  const [pick, setPick] = useState(0);
  const [press, setPress] = useState(true);
  const e = data.entities[pick];
  return (
    <>
      <Intro title="2. Every grammatical form, built once per match">
        <p><code>bbl/inflect.py</code> asks Claude for the full case paradigm (lemma, gender, whether it declines, full and short form per case),
          with the naming conventions for <b>{lang}</b> in the prompt. For Latvian players, <code>bbl/tezaurs.py</code> overwrites forms with the Tēzaurs morphology service.
          Then <code>bbl/press.py</code> layers press-verified forms from <code>data/names/press.json</code>. Cached as <code>data/cache/forms_{lang}_&lt;qid&gt;.json</code>; a native editor can fix one by editing the JSON.</p>
      </Intro>
      <div className="chips">
        {data.entities.map((x, i) => (
          <button key={x.name} className={`chip ${i === pick ? "on" : ""}`} onClick={() => setPick(i)}>
            {x.name} {x.press && <Badge tone="good">press</Badge>} {x.tezaurs && <Badge tone="info">Tēzaurs</Badge>}
          </button>
        ))}
      </div>
      <FormsTable e={e} press={press} setPress={setPress} />
    </>
  );
}

function FormsTable({ e, press, setPress }: { e: ExploreEntity; press: boolean; setPress: (b: boolean) => void }) {
  const t = press ? e.forms_press : e.forms;
  return (
    <div className="panel">
      <div className="panel-head">
        <div><b>{t.lemma}</b> <span className="muted">· {t.gender} · {t.declines ? "declines" : "does not decline"}</span></div>
        {e.press && (
          <div className="seg-toggle">
            <button className={!press ? "on" : ""} onClick={() => setPress(false)}>Drafted</button>
            <button className={press ? "on" : ""} onClick={() => setPress(true)}>After press check</button>
          </div>
        )}
      </div>
      <table className="grid">
        <thead><tr><th>Case</th><th>Full form</th><th>Short form (used in running copy)</th></tr></thead>
        <tbody>
          {t.forms.map((f, i) => {
            const before = e.forms.forms[i];
            const changed = press && e.press && (before.singular !== f.singular || before.short !== f.short);
            return (
              <tr key={f.case} className={changed ? "changed" : ""}>
                <td className="muted">{f.case}</td>
                <td>{f.singular}{changed && before.singular !== f.singular && <s className="was">{before.singular}</s>}</td>
                <td>{f.short}{changed && before.short !== f.short && <s className="was">{before.short}</s>}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="note">{t.usage_note}</p>
      {e.press && (
        <div className="evidence">
          <h5>Press evidence (shown to reviewers and judges, so a correct form is never flagged)</h5>
          <p>{e.press.evidence}</p>
          <ul>{e.press.sources.map((s) => <li key={s}><a href={s} target="_blank" rel="noreferrer">{s}</a></li>)}</ul>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- 3. locale pack
function Pack({ data, event }: { data: Explore; event: MatchEvent }) {
  const [tab, setTab] = useState<"style" | "glossary" | "examples" | "facts">("glossary");
  const [q, setQ] = useState("");
  const rows = data.pack.glossary.filter((g) => !q || JSON.stringify(g).toLowerCase().includes(q.toLowerCase()));
  return (
    <>
      <Intro title="3. Local knowledge, as plain files a linguist can edit">
        <p><code>bbl/locale_pack.py</code> loads four files per language. The glossary is filtered to <b>{event.sport}</b> plus general terms
          ({data.pack.glossary.length} of {data.pack.glossary_total} rows), and up to six examples are picked, same sport first ({data.pack.fewshot_picked} used).</p>
      </Intro>
      <div className="tabs">
        <button className={tab === "glossary" ? "on" : ""} onClick={() => setTab("glossary")}>Glossary <em>{data.pack.glossary.length}</em></button>
        <button className={tab === "style" ? "on" : ""} onClick={() => setTab("style")}>Style sheet <em>≈{fmtK(tok(data.pack.style.length))} tok</em></button>
        <button className={tab === "examples" ? "on" : ""} onClick={() => setTab("examples")}>Example buffs <em>{data.pack.fewshot.length}</em></button>
        <button className={tab === "facts" ? "on" : ""} onClick={() => setTab("facts")}>Validator facts</button>
      </div>
      {tab === "glossary" && <>
        <input className="search" placeholder="Filter terms…" value={q} onChange={(e) => setQ(e.target.value)} />
        <table className="grid">
          <thead><tr><th>English</th><th>Use this</th><th>Never this</th><th>Sport</th><th>Verified</th><th>Note</th></tr></thead>
          <tbody>
            {rows.map((g, i) => (
              <tr key={i}>
                <td>{g.en}</td><td><b>{g.term}</b></td>
                <td>{g.avoid?.map((a) => <span key={a} className="avoid">{a}</span>)}</td>
                <td className="muted">{g.sport}</td>
                <td>{g.verified ? <Badge tone="good" title="Calques of a verified term block the buff">verified</Badge> : <Badge>draft</Badge>}</td>
                <td className="small">{g.note} {g.source && <a href={g.source} target="_blank" rel="noreferrer">source</a>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </>}
      {tab === "style" && <pre className="prompt">{data.pack.style}</pre>}
      {tab === "examples" && <div className="examples">{data.pack.fewshot.map((f, i) => (
        <div key={i} className="example">
          <Badge>{String(f.sport)}</Badge> <Badge>{String(f.type)}</Badge>
          <p>{String(f.question)}</p>
          <div className="buffcard-opts">{(f.options as string[] | undefined)?.map((o) => <span key={o} className="buffcard-opt">{o}</span>)}</div>
          {f.status != null && <p className="muted small">{String(f.status)}</p>}
        </div>))}</div>}
      {tab === "facts" && <Json value={data.pack.facts} />}
    </>
  );
}

// ---------------------------------------------------------------- 4. prompt assembly
function Prompt({ data, run }: { data: Explore; run: RunState }) {
  const [which, setWhich] = useState<"D" | "B" | "A">("D");
  const d = data.prompt_d;
  const live = run.arms.D?.buff ? run.arms.D : run.arms.C?.buff ? run.arms.C : undefined;
  const firstGen = live ? Object.values(live.calls).find((c) => c.step === "C.generate") : undefined;
  return (
    <>
      <Intro title="4. How the context is built">
        <p><code>generate.system_for()</code> assembles one system prompt in this order: role, card rules, style sheet, glossary, name case tables, examples.
          The user message carries only the match facts and the moment. The stable system prompt is cached, so later buffs in the same match and language read it cheaply.
          Compare it with what today's two methods give the model.</p>
      </Intro>
      <div className="seg-toggle big">
        <button className={which === "D" ? "on" : ""} onClick={() => setWhich("D")}>New pipeline (C/D) <em>≈{fmtK(tok(d.system.length))} tok</em></button>
        <button className={which === "B" ? "on" : ""} onClick={() => setWhich("B")}>Today: sports_native (B) <em>≈{fmtK(tok(data.prompt_b.system.length))} tok</em></button>
        <button className={which === "A" ? "on" : ""} onClick={() => setWhich("A")}>Today: Translate button (A) <em>2 calls</em></button>
      </div>
      {which === "D" && <>
        <CompositionBar sections={d.sections} user={d.user} />
        <div className="compare">
          <div><h4>What the new prompt contains that today's don't</h4>
            <ul className="ticks">
              <li><b>Name case tables</b>: the exact form for every case, so names are never left in the nominative or respelled.</li>
              <li><b>Sport glossary with banned forms</b>: the term local broadcasters use, plus the calques to avoid.</li>
              <li><b>Style sheet</b>: register, question particles, numeral agreement, plural-only nouns, sport verbs.</li>
              <li><b>Examples</b> in house style, same sport first.</li>
              <li><b>A schema with reasoning notes</b>: the model must commit to each case choice before writing, and add an English meaning.</li>
            </ul></div>
          <div><h4>Output schema (validated, malformed output raises)</h4><Json value={data.schema} /></div>
        </div>
        <h4>System prompt, colour-coded by section</h4>
        <PromptText text={d.system} sections={d.sections} />
        <h4>User message</h4>
        <pre className="prompt">{d.user}</pre>
        {firstGen?.output && <>
          <h4>From your last run: what the model returned</h4>
          <p className="notes">{firstGen.output.reasoning_notes}</p>
          <BuffCard buff={firstGen.output.buff as Buff} />
        </>}
      </>}
      {which === "B" && <>
        <p className="note">Read live from <code>{data.prompt_b.source}</code>: generic native-writing rules for every language, with no glossary, no name forms, no examples and no checks afterwards.</p>
        <PromptText text={data.prompt_b.system} />
        <h4>User message</h4><pre className="prompt">{data.prompt_b.user}</pre>
      </>}
      {which === "A" && <>
        <p className="note">Step 1 writes the buff in English. Step 2 is JIL's Translate prompt, copied verbatim. It says to keep names "as-is", which breaks grammar in languages where names change form.</p>
        <h4>Call 1: write in English</h4><PromptText text={data.prompt_a.english_system} />
        <h4>Call 2: the Translate button prompt</h4><PromptText text={data.prompt_a.translate_system} />
      </>}
    </>
  );
}

// ---------------------------------------------------------------- 5. checks
function Checks({ data, event, lang, run }: { data: Explore; event: MatchEvent; lang: Lang; run: RunState }) {
  const seed = run.arms.A?.buff ?? run.arms.B?.buff ?? run.arms.D?.buff;
  const [buff, setBuff] = useState({ title: seed?.title ?? "", question: seed?.question ?? "", options: (seed?.options ?? ["", ""]).join("\n") });
  const [res, setRes] = useState<{ ms: number; issues: Issue[] } | null>(null);
  useEffect(() => { if (seed) setBuff({ title: seed.title, question: seed.question, options: seed.options.join("\n") }); }, [seed]);
  useEffect(() => {
    const id = setTimeout(() => {
      if (!buff.title && !buff.question) return setRes(null);
      postJSON<{ ms: number; issues: Issue[] }>("/api/validate", {
        event_id: event.id, lang, buff: { title: buff.title, question: buff.question, options: buff.options.split("\n").filter(Boolean) },
      }).then(setRes).catch(() => setRes(null));
    }, 350);
    return () => clearTimeout(id);
  }, [buff, event.id, lang]);
  return (
    <>
      <Intro title="5. Automatic checks: no model, under a second">
        <p><code>bbl/validators.py</code> and <code>bbl/spell.py</code> (Hunspell via spylls). Errors block the buff and go to repair; warnings travel with it.
          Type in the playground and the real validators run on every edit, with this match's name tables and the <b>{lang}</b> locale pack.
          {seed ? " It starts with a buff from your last run." : " Run a comparison first to start from a real buff."}</p>
      </Intro>
      <div className="compare">
        <div className="panel">
          <h4>Playground</h4>
          <label>Title<input value={buff.title} onChange={(e) => setBuff({ ...buff, title: e.target.value })} /></label>
          <label>Question<textarea rows={3} value={buff.question} onChange={(e) => setBuff({ ...buff, question: e.target.value })} /></label>
          <label>Options (one per line)<textarea rows={4} value={buff.options} onChange={(e) => setBuff({ ...buff, options: e.target.value })} /></label>
          <div className="result">
            {res ? <>
              <div className="muted small">{res.issues.length} issues in {res.ms} ms</div>
              {res.issues.length === 0 ? <Badge tone="good">clean</Badge> :
                <ul className="issues">{res.issues.map((i, k) => <li key={k}><Badge tone={sevTone(i.severity)}>{i.severity}</Badge> <code>{i.code}</code> {i.message}</li>)}</ul>}
            </> : <span className="muted">Type something…</span>}
          </div>
        </div>
        <div>
          <h4>Every rule</h4>
          <table className="grid">
            <thead><tr><th>Code</th><th>Severity</th><th>Catches</th></tr></thead>
            <tbody>{data.validator_rules.map((r) => <tr key={r.code}><td><code>{r.code}</code></td><td><Badge tone={sevTone(r.severity)}>{r.severity}</Badge></td><td>{r.what}</td></tr>)}</tbody>
          </table>
          <h4>This language's regex rules (locale.json)</h4>
          <ul className="issues">{((data.pack.facts.forbidden_patterns as { pattern: string; message: string; severity: string }[]) ?? []).map((p, i) => (
            <li key={i}><Badge tone={sevTone(p.severity)}>{p.severity}</Badge> {p.message} <code className="small">{p.pattern}</code></li>))}</ul>
        </div>
      </div>
    </>
  );
}

// ---------------------------------------------------------------- 6. review team
function Review({ data, run }: { data: Explore; run: RunState }) {
  const [open, setOpen] = useState<string | null>(null);
  const d = run.arms.D;
  const byKey = useMemo(() => Object.fromEntries(data.reviewers.map((r) => [r.key, r])), [data]);
  return (
    <>
      <Intro title="6. Five specialist reviewers and the orchestrator (arm D)">
        <p><code>bbl/reviewers.py</code>. Each reviewer owns one error type and sees only the reference data it needs, which keeps prompts short and findings focused.
          They run in parallel at low effort. The orchestrator is plain code, so every decision is logged and can be replayed.</p>
      </Intro>
      <div className="revgrid">
        {data.reviewers.map((r) => {
          const last = d?.reviewers.filter((x) => x.key === r.key).at(-1);
          return (
            <button key={r.key} className={`revcard ${open === r.key ? "on" : ""}`} onClick={() => setOpen(open === r.key ? null : r.key)}>
              <h4>{r.title}</h4>
              <p>{r.brief}</p>
              <div className="chips">{r.needs.map((n) => <Badge key={n} tone="info">sees: {n}</Badge>)}</div>
              <div className="muted small">{r.model} · ≈{fmtK(tok(r.chars))} tokens of context</div>
              {last && <div className="small">Last run: {last.findings?.length ? <Badge tone="warn">{last.findings.length} findings</Badge> : <Badge tone="good">pass</Badge>}</div>}
            </button>
          );
        })}
      </div>
      {open && <><h4>{byKey[open].title}: full system prompt</h4><PromptText text={byKey[open].system} /></>}
      <div className="compare">
        <div className="panel">
          <h4>Orchestrator rules, applied to every finding in order</h4>
          <ol className="rules">{data.orchestrator_rules.map((r) => <li key={r}>{r}</li>)}</ol>
        </div>
        <div className="panel">
          <h4>From your last D run</h4>
          {!d?.decisions.length ? <p className="muted">Run a comparison with D to see real decisions here.</p> :
            d.decisions.map((x) => (
              <div key={x.round} className="decision">
                <b>Round {x.round}</b> {x.publish ? <Badge tone="good">publish</Badge> : <Badge tone="bad">repair</Badge>}
                <span className="muted small"> {x.blocking.length} blocking · {x.advisory.length} advisory · {x.dismissed.length} dismissed</span>
                <ul className="issues">{[...x.blocking, ...x.advisory, ...x.dismissed].map((f, i) => (
                  <li key={i}><Badge>{f.reviewer}</Badge> <code>{f.span}</code> {f.problem} {f.why && <em className="why">({f.why})</em>}</li>))}</ul>
              </div>
            ))}
        </div>
      </div>
    </>
  );
}
