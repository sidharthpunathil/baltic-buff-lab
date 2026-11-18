"""Side-by-side HTML report: one row per (moment, language), one column per arm."""

from __future__ import annotations

import html
import json
from collections import defaultdict

from .config import LANG_NAMES


def to_dict(event: dict, r) -> dict:
    return {
        "event": f"{event['home']} vs {event['away']}",
        "sport": event["sport"],
        "moment": r.moment_id,
        "lang": r.lang,
        "arm": r.arm,
        "buff": r.buff.model_dump() if r.buff else None,
        "issues": r.issues,
        "judgement": r.judgement.model_dump() if r.judgement else None,
        "xjudgement": r.xjudgement.model_dump() if getattr(r, "xjudgement", None) else None,
        "mean_score": r.judgement.mean_score if r.judgement else None,
        "mqm_penalty": r.judgement.mqm_penalty if r.judgement else None,
        "trace": r.trace,
        "internal": getattr(r, "internal", None),
        "error": r.error,
    }


def _e(s) -> str:
    return html.escape(str(s))


def _x(r) -> str:
    x = getattr(r, "xjudgement", None)
    if not x:
        return ""
    errs = "; ".join(f"{e.severity} {e.category}: {e.span}" for e in x.errors) or "no errors"
    return f"<div class='sub'>2nd judge: <b>{x.mean_score}</b>/5 · MQM −{x.mqm_penalty} · {x.verdict} <span title='{_e(errs)}'>ⓘ</span></div>"


def _card(r) -> str:
    if r.error:
        return f"<div class='card err'>{_e(r.error)}</div>"
    b, j = r.buff, r.judgement
    opts = "".join(
        f"<li class='{'ok' if b.correct_index == i else ''}'>{_e(o)}</li>" for i, o in enumerate(b.options)
    )
    errs = "".join(
        f"<li><span class='sev {e.severity}'>{e.severity}</span> <b>{_e(e.category)}</b> “{_e(e.span)}”: {_e(e.explanation)} → <i>{_e(e.suggested_fix)}</i></li>"
        for e in j.errors
    ) or "<li class='muted'>no errors found</li>"
    issues = "".join(f"<li>{_e(i)}</li>" for i in r.issues) or "<li class='muted'>clean</li>"
    trace = ""
    if r.trace and len(r.trace) > 1:
        rounds = "".join(
            f"<div class='round'><b>round {t['round']}</b>: {_e(t['buff']['question'])} | {_e(' / '.join(t['buff']['options']))}"
            f"<br><span class='muted'>judge {t['judge']['verdict']}, issues: {_e('; '.join(t['issues']) or 'none')}</span></div>"
            for t in r.trace
        )
        trace = f"<details><summary>repair trace ({len(r.trace)} rounds)</summary>{rounds}</details>"
    rewrite = ""
    if j.native_rewrite:
        nr = j.native_rewrite
        rewrite = f"<details><summary>judge's native rewrite</summary><p>{_e(nr.title)} — {_e(nr.question)}</p><p>{_e(' / '.join(nr.options))}</p></details>"
    team = ""
    internal = getattr(r, "internal", None) or {}
    for d in internal.get("team_decisions", []):
        rows = "".join(
            f"<li><b>{_e(x['reviewer'])}</b> {_e(x['severity'])} “{_e(x['span'])}” {_e(x.get('why') or '→ ' + x['fix'])}</li>"
            for x in d["blocking"] + d["dismissed"]
        ) or "<li class='muted'>all reviewers passed</li>"
        team += f"<details><summary>team round {d['round']}: {len(d['blocking'])} blocking, {len(d['dismissed'])} dismissed (ran {', '.join(f'{k}:{v}' for k, v in d['ran'].items())})</summary><ul>{rows}</ul></details>"
    return f"""<div class='card'>
  <div class='score'><span class='big'>{j.mean_score}</span>/5 · MQM −{j.mqm_penalty} · <span class='v {j.verdict}'>{j.verdict}</span></div>
  {_x(r)}
  <div class='sub'>gram {j.grammar} · nat {j.naturalness} · term {j.terminology} · fact {j.faithfulness} · eng {j.engagement}</div>
  <h4>{_e(b.title)}</h4><p class='q'>{_e(b.question)}</p><ol>{opts}</ol>
  <p class='reveal'>{_e(b.reveal)}</p>
  <p class='gloss'>EN gloss: {_e(b.english_gloss)}</p>
  <details><summary>judge errors ({len(j.errors)})</summary><ul>{errs}</ul></details>
  <details><summary>validators ({len(r.issues)})</summary><ul>{issues}</ul></details>
  {rewrite}{trace}{team}
</div>"""


CSS = """
:root{--bg:#f6f7fb;--fg:#14151a;--muted:#6b6f7b;--card:#fff;--line:#e3e5ec;--ok:#0f7a3d;--bad:#b42318;--warn:#9a6700;--brand:#3a30f0}
@media (prefers-color-scheme:dark){:root{--bg:#0d0e13;--fg:#e8e9ee;--muted:#9096a3;--card:#171922;--line:#2a2d3a;--ok:#5fd38d;--bad:#ff8a80;--warn:#f5c451;--brand:#8f88ff}}
body{background:var(--bg);color:var(--fg);font:14px/1.45 -apple-system,system-ui,sans-serif;margin:0;padding:24px 16px}
h1{margin:0 0 4px} .muted{color:var(--muted)} table{border-collapse:collapse;margin:12px 0}
td,th{border:1px solid var(--line);padding:4px 8px;text-align:left}
.row{margin:28px 0} .row h3{margin:0 0 8px} .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.card.err{color:var(--bad)} .arm{font-weight:600;color:var(--brand);margin-bottom:6px}
.big{font-size:22px;font-weight:700} .sub{color:var(--muted);font-size:12px} .q{font-weight:600}
li.ok{color:var(--ok);font-weight:600} .gloss,.reveal{color:var(--muted);font-size:12px}
.sev{font-size:11px;padding:1px 5px;border-radius:6px;border:1px solid var(--line)} .sev.major,.sev.critical{color:var(--bad)} .sev.minor{color:var(--warn)}
.v.approve{color:var(--ok)} .v.revise{color:var(--warn)} .v.reject{color:var(--bad)} .round{margin:6px 0}
"""


def render(all_results, settings, usage) -> str:
    rows: dict[tuple, dict] = defaultdict(dict)
    meta = {}
    for x in all_results:
        r, ev = x["result"], x["event"]
        key = (f"{ev['home']} vs {ev['away']}", r.moment_id, r.lang)
        rows[key][r.arm] = r
        moment = next(m for m in ev["moments"] if m["id"] == r.moment_id)
        meta[key] = moment
    # summary table
    agg: dict[tuple, list] = defaultdict(list)
    for x in all_results:
        r = x["result"]
        if r.judgement:
            agg[(r.lang, r.arm)].append(r.judgement)
    summ = "".join(
        f"<tr><td>{LANG_NAMES[l]}</td><td>{a}</td><td>{len(js)}</td><td>{sum(j.mean_score for j in js)/len(js):.2f}</td>"
        f"<td>{sum(j.naturalness for j in js)/len(js):.2f}</td><td>{sum(j.mqm_penalty for j in js)/len(js):.1f}</td>"
        f"<td>{sum(j.verdict=='approve' for j in js)}/{len(js)}</td></tr>"
        for (l, a), js in sorted(agg.items())
    )
    body = []
    for key, arms in rows.items():
        m = meta[key]
        cards = "".join(f"<div><div class='arm'>{_e(a)}</div>{_card(arms[a])}</div>" for a in sorted(arms))
        body.append(
            f"<div class='row'><h3>{_e(key[0])} · {LANG_NAMES[key[2]]} · {_e(m['buff_type'])}</h3>"
            f"<div class='muted'>moment: {_e(m['text'])} ({_e(m['state'])})</div><div class='grid'>{cards}</div></div>"
        )
    return f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Baltic Buff Lab</title><style>{CSS}</style></head><body>
<h1>Baltic Buff Lab: A/B/C</h1>
<p class='muted'>A = today's translate button · B = today's sports_native pack · C = native-first + locale pack + names + validators + judge + repair.
Generator {settings.gen_model}, baseline {settings.baseline_model}, blind judge {settings.judge_model}. LLM calls {usage.calls}, tokens in {usage.input_tokens} / out {usage.output_tokens}.
Caveat: the judge is an LLM from the same family and sees the same style guide as arm C; treat scores as a triage signal and confirm with native raters.</p>
<table><tr><th>language</th><th>arm</th><th>n</th><th>mean 1-5</th><th>naturalness</th><th>MQM penalty</th><th>approved</th></tr>{summ}</table>
{''.join(body)}
<script>/* data */ window.BBL={json.dumps([to_dict(x['event'], x['result']) for x in all_results], ensure_ascii=False).replace('</', '<\\/')};</script>
</body></html>"""
