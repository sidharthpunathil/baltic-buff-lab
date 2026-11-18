import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import { getJSON, streamRun, type ArmKey, type Explore, type Lang, type Meta } from "./api";
import { ExploreView } from "./ExploreView";
import { LiveView } from "./LiveView";
import { emptyRun, reduce, totals } from "./run";
import { usd } from "./ui";

const FLAGS: Record<Lang, string> = { lt: "🇱🇹", lv: "🇱🇻", et: "🇪🇪" };

export function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [eventId, setEventId] = useState("");
  const [momentId, setMomentId] = useState("");
  const [lang, setLang] = useState<Lang>("lv");
  const [arms, setArms] = useState<ArmKey[]>(["A", "B", "D"]);
  const [judge, setJudge] = useState(true);
  const [custom, setCustom] = useState<{ state: string; text: string; buff_type: string } | null>(null);
  const [view, setView] = useState<"live" | "inside">("live");
  const [explore, setExplore] = useState<Explore | null>(null);
  const [run, dispatch] = useReducer(reduce, emptyRun);
  const [runStartedAt, setRunStartedAt] = useState(0);
  const abort = useRef<AbortController | null>(null);

  useEffect(() => {
    getJSON<Meta>("/api/meta").then((m) => {
      setMeta(m);
      const hockey = m.events.find((e) => e.sport.includes("hockey")) ?? m.events[0];
      setEventId(hockey.id);
      setMomentId(hockey.moments[0].id);
    }).catch((e) => setErr(String(e)));
  }, []);

  const event = meta?.events.find((e) => e.id === eventId);
  const moment = event?.moments.find((m) => m.id === momentId) ?? event?.moments[0];

  useEffect(() => {
    if (!event) return;
    setExplore(null);
    getJSON<Explore>(`/api/explore?event_id=${event.id}&lang=${lang}&moment_id=${moment?.id ?? ""}`)
      .then(setExplore).catch((e) => setErr(String(e)));
  }, [event, lang, moment?.id]);

  const start = useCallback(async () => {
    if (!event || !moment) return;
    abort.current?.abort();
    const ctrl = new AbortController();
    abort.current = ctrl;
    setRunStartedAt(performance.now());
    setView("live");
    try {
      await streamRun({ event_id: event.id, lang, arms, judge,
        moment: { id: custom ? "" : moment.id, ...(custom ?? { buff_type: moment.buff_type, state: moment.state, text: moment.text }) } },
        dispatch, ctrl.signal);
    } catch (e) {
      if (!ctrl.signal.aborted) dispatch({ t: "fatal", error: String(e) });
    }
  }, [event, moment, lang, arms, judge, custom]);

  const stop = () => { abort.current?.abort(); dispatch({ t: "done" }); };
  const running = run.status === "running";
  const spent = Object.values(run.arms).reduce((n, a) => n + (a ? totals(a).cost : 0), 0);

  if (err && !meta) return <div className="fatal">Can't reach the lab server: {err}. Start it with <code>app/run.sh</code>.</div>;
  if (!meta || !event || !moment) return <div className="fatal">Loading…</div>;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="logo">B</span>
          <div><h1>Buff Lab Live</h1><p>Baltic buffs: today's methods vs the new pipeline, generated live</p></div>
        </div>
        <nav className="tabs main">
          <button className={view === "live" ? "on" : ""} onClick={() => setView("live")}>Live comparison</button>
          <button className={view === "inside" ? "on" : ""} onClick={() => setView("inside")}>Pipeline inside</button>
        </nav>
      </header>

      <section className="controls">
        <label className="field">
          <span>Match</span>
          <select value={eventId} onChange={(e) => { const ev = meta.events.find((x) => x.id === e.target.value)!; setEventId(ev.id); setMomentId(ev.moments[0].id); setCustom(null); }}>
            {meta.events.map((e) => <option key={e.id} value={e.id}>{e.home} vs {e.away} · {e.sport}</option>)}
          </select>
        </label>
        <label className="field grow">
          <span>Live moment</span>
          <select value={custom ? "custom" : momentId} onChange={(e) => {
            if (e.target.value === "custom") setCustom({ state: moment.state, text: moment.text, buff_type: moment.buff_type });
            else { setMomentId(e.target.value); setCustom(null); }
          }}>
            {event.moments.map((m) => <option key={m.id} value={m.id}>{m.state}: {m.text}</option>)}
            <option value="custom">Write your own moment…</option>
          </select>
        </label>
        <div className="field">
          <span>Fan language</span>
          <div className="seg-toggle">
            {(Object.keys(meta.langs) as Lang[]).map((l) => (
              <button key={l} className={lang === l ? "on" : ""} onClick={() => setLang(l)} title={meta.langs[l]}>{FLAGS[l]} {l.toUpperCase()}</button>
            ))}
          </div>
        </div>
        <div className="field">
          <span>Methods</span>
          <div className="seg-toggle">
            {meta.arms.map((a) => (
              <button key={a.key} className={`${arms.includes(a.key) ? "on" : ""} ${a.kind}`} title={`${a.name}: ${a.how}`}
                onClick={() => setArms((cur) => cur.includes(a.key) ? cur.filter((x) => x !== a.key) : [...cur, a.key].sort() as ArmKey[])}>
                {a.key}
              </button>
            ))}
          </div>
        </div>
        <label className="check" title="Score every final buff with a fresh, blind Claude judge (adds one call per method)">
          <input type="checkbox" checked={judge} onChange={(e) => setJudge(e.target.checked)} /> Blind judge
        </label>
        {running
          ? <button className="btn stop" onClick={stop}>Stop</button>
          : <button className="btn run" onClick={start} disabled={!arms.length}>Run ▸</button>}
      </section>

      {custom && (
        <section className="custom">
          <label className="field"><span>Score / state</span><input value={custom.state} onChange={(e) => setCustom({ ...custom, state: e.target.value })} /></label>
          <label className="field grow"><span>What just happened (English, like an operator would type it)</span>
            <input value={custom.text} onChange={(e) => setCustom({ ...custom, text: e.target.value })} /></label>
          <label className="field"><span>Buff type</span>
            <select value={custom.buff_type} onChange={(e) => setCustom({ ...custom, buff_type: e.target.value })}>
              <option>prediction</option><option>poll</option><option>quiz</option>
            </select></label>
        </section>
      )}

      <section className="context-strip">
        <span><b>{event.competition}</b></span>
        <span>{custom ? custom.state : moment.state}</span>
        <span>{custom ? custom.text : moment.text}</span>
        <span className="muted">{(custom ?? moment).buff_type}</span>
        {run.status !== "idle" && <span className="spent">spent {usd(spent)}</span>}
      </section>

      <main>
        {view === "live"
          ? <LiveView run={run} arms={meta.arms} runStartedAt={runStartedAt} />
          : <ExploreView data={explore} event={event} lang={lang} run={run} />}
      </main>

      <footer className="foot">
        Runs the real <code>bbl/</code> code. Writer and reviewers: {meta.settings.gen_model} · today's methods: {meta.settings.baseline_model} ·
        judge: {meta.settings.judge_model} ({meta.settings.judge_effort}) · repairs: up to {meta.settings.max_repairs}.
        The native-ear reviewer runs on Claude here, and the second-vendor judge is off, to keep live runs fast.
      </footer>
    </div>
  );
}
