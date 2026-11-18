"""Build the side-by-side examples gallery from real run results.

Every column uses the same generator model (claude-opus-5-5), so differences come from the method:
  A  today's Translate button       out/run-20261117-232937 (ablation run)
  B  today's sports_native prompt   out/run-20261117-235224 (round 2)
  C  round-1 native-first pipeline  out/run-20261117-235224
  D  review-team pipeline           out/run-20261117-235224

Writes docs/examples.html (self-contained page) and docs/EXAMPLES.md.
Usage: python3 -I tools/build_examples.py
"""

from __future__ import annotations

import html
import json
import pathlib
import re
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUN_A = ROOT / "out/run-20261117-232937/results.json"
RUN_R2 = ROOT / "out/run-20261117-235224/results.json"
DOCS = ROOT / "docs"
EVENTS = {json.loads(p.read_text())["home"]: json.loads(p.read_text()) for p in (ROOT / "samples/events").glob("*.json")}

ARMS = [
    ("A.translate", "A", "Today: Translate button", "English buff, then JIL's translate prompt"),
    ("B.native", "B", "Today: native prompt", "sports_native pack, one call"),
    ("C.baltic", "C", "New: native-first pipeline", "locale pack + names + checks + repair"),
    ("D.team", "D", "New: review-team pipeline", "C + press names + 5 specialist reviewers"),
]
LANG = {"lt": "Lithuanian", "lv": "Latvian", "et": "Estonian"}
DIMS = ["grammar", "naturalness", "terminology", "faithfulness", "engagement"]


def load():
    rows = [r for r in json.loads(RUN_A.read_text()) if r["arm"] == "A.translate"]
    rows += json.loads(RUN_R2.read_text())
    by = defaultdict(dict)
    for r in rows:
        by[(r["event"], r["moment"], r["lang"])][r["arm"]] = r
    return by


def moment_of(event_name: str, mid: str) -> tuple[dict, dict]:
    home = event_name.split(" vs ")[0]
    ev = next(e for h, e in EVENTS.items() if home.startswith(h) or h.startswith(home))
    return ev, next(m for m in ev["moments"] if m["id"] == mid)


def score(j: dict | None) -> float | None:
    return round(sum(j[d] for d in DIMS) / len(DIMS), 2) if j else None


def penalty(j: dict | None) -> int:
    w = {"minor": 1, "major": 5, "critical": 10}
    return sum(w[e["severity"]] for e in j["errors"]) if j else 0


def mark(text: str, errors: list[dict]) -> str:
    out = html.escape(text)
    for e in sorted(errors, key=lambda e: -len(e["span"])):
        span = html.escape(e["span"].strip())
        if len(span) >= 2 and span in out:
            out = out.replace(span, f'<mark class="{e["severity"]}" title="{html.escape(e["category"] + ": " + e["explanation"])}">{span}</mark>', 1)
    return out


def card(r: dict | None, label: tuple) -> str:
    key, letter, name, sub = label
    if not r or not r.get("buff"):
        return f'<article class="card missing"><header><span class="letter">{letter}</span><div><b>{name}</b><small>{sub}</small></div></header><p class="muted">No result{": " + html.escape(r["error"]) if r and r.get("error") else ""}</p></article>'
    b, j, x = r["buff"], r["judgement"], r.get("xjudgement")
    errs = j["errors"] if j else []
    opts = "".join(
        f'<li class="{"correct" if b.get("correct_index") == i else ""}">{mark(o, errs)}</li>' for i, o in enumerate(b["options"])
    )
    verdict = j["verdict"] if j else "n/a"
    xv = f'<span class="x">2nd judge (Gemini): {x["verdict"]}, {score(x)}</span>' if x else '<span class="x muted">2nd judge: no answer</span>'
    err_list = "".join(
        f'<li><span class="sev {e["severity"]}">{e["severity"]}</span> <b>{html.escape(e["category"])}</b>: “{html.escape(e["span"])}”. {html.escape(e["explanation"])} <i>Fix: {html.escape(e["suggested_fix"])}</i></li>'
        for e in errs
    ) or '<li class="muted">No errors found by the judge.</li>'
    extra = ""
    if r["arm"] == "D.team" and r.get("internal"):
        rounds = r["internal"].get("team_decisions", [])
        steps = []
        for d in rounds:
            bl = "; ".join(f'{b2["reviewer"]}: “{b2["span"]}” → {b2["fix"]}' for b2 in d["blocking"])
            val = "; ".join(d["validator"])
            dis = "; ".join(f'{b2["reviewer"]} “{b2["span"]}” ({b2["why"]})' for b2 in d["dismissed"])
            steps.append(
                f'<li>Round {d["round"]}: '
                + (f"blocked by reviewers: {html.escape(bl)}. " if bl else "")
                + (f"validator: {html.escape(val)}. " if val else "")
                + (f"dismissed: {html.escape(dis)}. " if dis else "")
                + ("passed all checks." if not bl and not val else "sent back for repair.")
                + "</li>"
            )
        extra = f'<details><summary>Review team, {len(rounds)} round{"s" if len(rounds) != 1 else ""}</summary><ul>{"".join(steps)}</ul></details>'
    elif r["arm"] == "C.baltic" and r.get("trace") and len(r["trace"]) > 1:
        extra = f'<details><summary>Repair loop, {len(r["trace"])} rounds</summary><ul>' + "".join(
            f'<li>Round {t["round"]}: {html.escape(t["buff"]["question"])}</li>' for t in r["trace"]
        ) + "</ul></details>"
    gloss = html.escape(b.get("english_gloss") or "")
    return f"""<article class="card v-{verdict}">
<header><span class="letter">{letter}</span><div><b>{name}</b><small>{sub}</small></div></header>
<div class="score"><b>{score(j)}</b>/5 <span class="verdict {verdict}">{verdict}</span> <span class="muted">MQM −{penalty(j)}</span></div>
{xv}
<h4>{mark(b["title"], errs)}</h4>
<p class="q">{mark(b["question"], errs)}</p>
<ol>{opts}</ol>
<p class="reveal">{mark(b["reveal"], errs)}</p>
<details><summary>English meaning</summary><p class="gloss">{gloss}</p></details>
<details{' open' if any(e["severity"] != "minor" for e in errs) else ''}><summary>Judge errors ({len(errs)})</summary><ul class="errs">{err_list}</ul></details>
{extra}
</article>"""


def provenance() -> tuple[str, str]:
    """'How we got these results': pipeline, data, libraries, models, scoring, research, each with links.
    Counts are read from the data files so the page stays true when the data changes. Relative links
    point at files in this lab (it is gitignored, so there is no public repository for it)."""
    gl = {l: json.loads((ROOT / f"data/glossary/{l}.json").read_text()) for l in LANG}
    fs = {l: json.loads((ROOT / f"locales/{l}/fewshot.json").read_text()) for l in LANG}
    rules = {l: len(json.loads((ROOT / f"locales/{l}/locale.json").read_text()).get("forbidden_patterns", [])) for l in LANG}
    press = {l: len(v) for l, v in json.loads((ROOT / "data/names/press.json").read_text()).items() if not l.startswith("_")}
    gl_line = ", ".join(f"{LANG[l]} {len(gl[l])} ({sum(1 for g in gl[l] if g.get('verified'))} source-verified)" for l in LANG)
    press_line = ", ".join(f"{LANG[l]} {press.get(l, 0)}" for l in LANG)
    comps = ", ".join(e["competition"].split(" (")[0] for e in EVENTS.values())
    L = lambda *pairs: list(pairs)  # noqa: E731  (label, url) pairs

    steps = [
        ("1. Real names", "Every team and player is looked up on Wikidata, which stores how each language’s editors spell them (lt “Kauno Žalgiris”, lv Kauņas “Žalgiris”).",
         L(("bbl/entities.py", "../bbl/entities.py"))),
        ("2. Every grammatical form", "A table of every case form per name is built once per match: drafted by Claude, overwritten by the Tēzaurs morphology service for Latvian players, then corrected with forms checked against native sports press.",
         L(("bbl/inflect.py", "../bbl/inflect.py"), ("bbl/tezaurs.py", "../bbl/tezaurs.py"), ("bbl/press.py", "../bbl/press.py"))),
        ("3. Local knowledge in the prompt", "A style sheet, a sport glossary and example buffs per language go into one prompt, with the match facts.",
         L(("bbl/locale_pack.py", "../bbl/locale_pack.py"))),
        ("4. Written, not translated", "Claude writes the buff directly in the fan’s language and adds an English meaning for the operator. Output must match a fixed schema.",
         L(("bbl/generate.py", "../bbl/generate.py"), ("bbl/schemas.py", "../bbl/schemas.py"))),
        ("5. Automatic checks", "Spelling (Hunspell), missing accents, letters from the wrong Baltic alphabet, banned literal translations, plural-only nouns, register and card length, in milliseconds.",
         L(("bbl/validators.py", "../bbl/validators.py"), ("bbl/spell.py", "../bbl/spell.py"))),
        ("6. Five specialist reviewers (D only)", "Grammar, sport terms, names, native ear and facts check the buff in parallel. A plain-code orchestrator drops false alarms and sends real problems back for at most two repairs.",
         L(("bbl/reviewers.py", "../bbl/reviewers.py"), ("bbl/pipeline.py", "../bbl/pipeline.py"))),
    ]
    data = [
        ("Wikidata", "Team and player labels in lt, lv, et, through the wbgetentities API.",
         L(("wikidata.org", "https://www.wikidata.org"), ("API docs", "https://www.wikidata.org/w/api.php?action=help&modules=wbgetentities"))),
        ("Tēzaurs morphology API", "Rule-based Latvian name declension, public and keyless.",
         L(("morpho-api.tezaurs.lv", "https://morpho-api.tezaurs.lv"), ("tezaurs.lv", "https://tezaurs.lv"))),
        ("Native sports press", f"Name forms checked against these sites, with a source URL per form in the data file. Entries: {press_line}.",
         L(("15min", "https://www.15min.lt"), ("sportas.lt", "https://www.sportas.lt"), ("basketnews.lt", "https://www.basketnews.lt"), ("LRT sport", "https://www.lrt.lt/naujienos/sportas"),
           ("Delfi", "https://www.delfi.lv"), ("Sportacentrs", "https://sportacentrs.com"), ("ERR sport", "https://sport.err.ee"), ("Postimees sport", "https://sport.postimees.ee"),
           ("data/names/press.json", "../data/names/press.json"))),
        ("Sport glossaries", f"Terms per language with the forms to avoid and a source per term: {gl_line}.",
         L(("VLKK term bank (lt)", "https://terminai.vlkk.lt"), ("Stonkus sports dictionary (lt)", "https://virtualibiblioteka.lka.lt/discovery/fulldisplay/alma990000051943108479/370LABT_LKA:LKA"),
           ("LSPA/RSU English-Latvian sports dictionary (lv, PDF)", "https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf"),
           ("EKI language guide (et)", "https://eki.ee/teatmik/voornimede-kaanamine"), ("Sõnaveeb (et)", "https://sonaveeb.ee"),
           ("lt.json", "../data/glossary/lt.json"), ("lv.json", "../data/glossary/lv.json"), ("et.json", "../data/glossary/et.json"))),
        ("Style sheets and rules", f"Register, numerals, plural-only nouns, club conventions and translationese tells, plus regex rules (lt {rules['lt']}, lv {rules['lv']}, et {rules['et']}).",
         L(("lt style", "../locales/lt/style.md"), ("lv style", "../locales/lv/style.md"), ("et style", "../locales/et/style.md"))),
        ("Example buffs", f"{len(fs['lt'])} per language in house style. Research drafts, not yet reviewed by native speakers.",
         L(("lt", "../locales/lt/fewshot.json"), ("lv", "../locales/lv/fewshot.json"), ("et", "../locales/et/fewshot.json"))),
        ("Hunspell dictionaries", "The LibreOffice lt_LT, lv_LV and et_EE dictionaries, as shipped in the phunspell package.",
         L(("LibreOffice/dictionaries", "https://github.com/LibreOffice/dictionaries"), ("phunspell", "https://github.com/dvwright/phunspell"))),
        ("Test matches", f"Three simulated matches with real teams and players: {comps}. Two live moments each.",
         L(("samples/events/", "../samples/events/"))),
    ]
    libs = [
        ("anthropic (Python SDK)", "Every Claude call, with structured output (messages.parse) and prompt caching.", L(("GitHub", "https://github.com/anthropics/anthropic-sdk-python"))),
        ("pydantic", "The schemas every model answer must match: buff, case table, review finding, judgement.", L(("GitHub", "https://github.com/pydantic/pydantic"))),
        ("google-genai", "Gemini calls for the second judge and the native-ear reviewer.", L(("GitHub", "https://github.com/googleapis/python-genai"))),
        ("spylls", "Pure-Python Hunspell engine for spell checking all three languages.", L(("GitHub", "https://github.com/zverok/spylls"))),
        ("phunspell", "Packages the Hunspell dictionaries spylls reads.", L(("GitHub", "https://github.com/dvwright/phunspell"))),
        ("urllib (standard library)", "Wikidata and Tēzaurs requests. Wikimedia blocked the httpx client.", L(("docs", "https://docs.python.org/3/library/urllib.request.html"))),
        ("pytest", "22 offline tests for validators, press overrides and the orchestrator.", L(("GitHub", "https://github.com/pytest-dev/pytest"), ("tests/", "../tests/"))),
        ("rich", "Terminal tables for run summaries.", L(("GitHub", "https://github.com/Textualize/rich"))),
        ("uv", "Python environment and dependencies.", L(("GitHub", "https://github.com/astral-sh/uv"), ("pyproject.toml", "../pyproject.toml"))),
        ("Playwright", "Rendering checks for these pages and the decks.", L(("GitHub", "https://github.com/microsoft/playwright-python"))),
        ("Tavily search", "Research and the press checks for name spellings.", L(("docs", "https://docs.tavily.com"))),
    ]
    models = [
        ("claude-opus-5-5", "Writes the buffs for all four columns here, builds the case tables, runs four of the five reviewers (and the fifth when Gemini is overloaded) and is the main judge.",
         L(("Claude models", "https://docs.claude.com/en/docs/about-claude/models/overview"))),
        ("Gemini 3.6 Flash, falling back to 3.5 Flash-Lite", "The second, cross-vendor judge and the native-ear reviewer. Overloaded often, so it falls back to Claude.",
         L(("Gemini models", "https://ai.google.dev/gemini-api/docs/models"))),
        ("claude-sonnet-5-5", "The model JIL’s backend uses today; used in an earlier run to show today’s results on today’s model.",
         L(("Claude models", "https://docs.claude.com/en/docs/about-claude/models/overview"))),
    ]
    evals = [
        ("Same 18 moments, same model for all four columns, so differences come from the method.", L(("bbl/judge.py", "../bbl/judge.py"))),
        ("The judge is blind: it sees the match facts and the card, never the English source or which column wrote it.", L()),
        ("It lists errors MQM-style, the method WMT uses (GEMBA-MQM), with severities, and scores grammar, naturalness, terminology, facts and engagement from 1 to 5. Approved means no major or critical errors.",
         L(("GEMBA-MQM paper", "https://arxiv.org/abs/2310.13988"), ("WMT25", "https://machinetranslate.org/wmt25"))),
        ("A second judge from another vendor (Gemini) scores the same cards to check for same-family bias. It scored most B, C and D cards; column A comes from an earlier run that did not use it.", L()),
        ("Judges get the press evidence, so a correctly spelled name isn’t marked wrong. Column A was scored before this was added, which is why one A card shows a false flag on “Donnarumma”.", L()),
        ("Raw results: every buff, issue, judgement, repair round and team decision.",
         L(("run A", "../out/run-20261117-232937/results.json"), ("run B, C, D", "../out/run-20261117-235224/results.json"))),
    ]
    research = [
        ("research/01: grammar traps, club and name conventions, sport terms and translationese tells per language, with sources.", L(("research/01", "../research/01-linguistics-and-terminology.md"))),
        ("research/02: which tools and models work for these languages, with endpoints we tested.",
         L(("research/02", "../research/02-tools-models-data.md"), ("EuroEval leaderboards", "https://euroeval.com/leaderboards"), ("EuroEval data on GitHub", "https://github.com/EuroEval/leaderboards"),
           ("EKI Estonian leaderboard data", "https://github.com/keeleinstituut/leaderboard-data-ui"), ("NoDaLiDa 2025 Baltic LLM paper", "https://aclanthology.org/2025.nodalida-1.30.pdf"),
           ("arXiv 2501.03952", "https://arxiv.org/abs/2501.03952"))),
        ("research/03: how Duolingo, Babbel, Sportradar and WMT get quality in many languages, ranked into what we should copy.",
         L(("research/03", "../research/03-methods-and-quality-loops.md"), ("Duolingo on LLM lessons", "https://blog.duolingo.com/large-language-model-duolingo-lessons"))),
        ("Next to try: TildeOpen-30b, an open model built for these languages, as a grammar ranker.", L(("Hugging Face", "https://huggingface.co/TildeAI/TildeOpen-30b"))),
    ]

    def links_html(pairs):
        if not pairs:
            return ""
        return '<span class="links">' + " ".join(
            f'<a href="{html.escape(u)}"{" target=_blank rel=noopener" if u.startswith("http") else ""}>{html.escape(t)}{" ↗" if u.startswith("http") else ""}</a>' for t, u in pairs
        ) + "</span>"

    def links_md(pairs):
        return (" " + " · ".join(f"[{t}]({u})" for t, u in pairs)) if pairs else ""

    li = lambda items: "".join(f"<li>{x}</li>" for x in items)  # noqa: E731
    html_out = f"""<section class="how" id="how">
<h2>How we got these results</h2>
<p class="lead">Nothing here is hand-picked or retyped: the cards below come straight from the run results. This is what produced them, with links to every source. Links marked ↗ open the public source; the others open files in this lab.</p>
<h3>The pipeline behind columns C and D</h3>
<div class="steps">{''.join(f'<div class="step"><b>{html.escape(t)}</b><p>{html.escape(d)}</p>{links_html(ls)}</div>' for t, d, ls in steps)}</div>
<div class="cols">
<div><h3>Data</h3><ul>{li(f'<b>{html.escape(n)}</b>: {html.escape(d)}{links_html(ls)}' for n, d, ls in data)}</ul></div>
<div><h3>Libraries and services</h3><ul>{li(f'<b>{html.escape(n)}</b>: {html.escape(d)}{links_html(ls)}' for n, d, ls in libs)}</ul>
<h3>Models</h3><ul>{li(f'<b>{html.escape(n)}</b>: {html.escape(d)}{links_html(ls)}' for n, d, ls in models)}</ul></div>
</div>
<div class="cols">
<div><h3>How the cards were scored</h3><ul>{li(html.escape(x) + links_html(ls) for x, ls in evals)}</ul></div>
<div><h3>Research behind the rules</h3><ul>{li(html.escape(x) + links_html(ls) for x, ls in research)}</ul>
<p class="muted">Full details, data formats and every rule: <a href="HOW-IT-WORKS.md">docs/HOW-IT-WORKS.md</a>. The lab lives on the feature/baltic-language-research branch and is gitignored, so it has no public repository.</p></div>
</div>
</section>"""
    md_out = ("## How we got these results\n\n"
              "Nothing here is hand-picked or retyped: the tables come straight from the run results. "
              "Links to public sources go to the web; the others are files in this lab (gitignored, so there is no public repository).\n\n"
              "### The pipeline behind C and D\n\n" + "\n".join(f"- **{t}**: {d}{links_md(ls)}" for t, d, ls in steps) +
              "\n\n### Data\n\n" + "\n".join(f"- **{n}**: {d}{links_md(ls)}" for n, d, ls in data) +
              "\n\n### Libraries and services\n\n" + "\n".join(f"- **{n}**: {d}{links_md(ls)}" for n, d, ls in libs) +
              "\n\n### Models\n\n" + "\n".join(f"- **{n}**: {d}{links_md(ls)}" for n, d, ls in models) +
              "\n\n### How the cards were scored\n\n" + "\n".join(f"- {x}{links_md(ls)}" for x, ls in evals) +
              "\n\n### Research behind the rules\n\n" + "\n".join(f"- {x}{links_md(ls)}" for x, ls in research) +
              "\n\nFull details: [`docs/HOW-IT-WORKS.md`](HOW-IT-WORKS.md).\n\n## Every example\n")
    return html_out, md_out

CSS = """
:root{--bg:#F4F5EE;--fg:#12132B;--muted:#5A5D78;--card:#FFFFFF;--line:#D9DBCF;--brand:#3A30F0;--ok:#0E7A3E;--warn:#9A5B00;--bad:#B3261E;--markmaj:#FFD7C2;--markmin:#FFF1B8}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0F1022;--fg:#ECEDF6;--muted:#A3A7C2;--card:#191B33;--line:#2C2F52;--brand:#9C96FF;--ok:#6FD99A;--warn:#F2C25B;--bad:#FF8A80;--markmaj:#6B2E1A;--markmin:#5A4A12}}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,sans-serif}
.wrap{max-width:1400px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:34px;margin:0 0 8px} h2{font-size:22px;margin:40px 0 4px} .muted{color:var(--muted)}
.lead{max-width:860px;color:var(--muted)}
.filters{position:sticky;top:0;z-index:5;background:var(--bg);padding:12px 0;border-bottom:1px solid var(--line);display:flex;gap:8px;flex-wrap:wrap}
.filters button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:8px 14px;font:inherit;cursor:pointer;min-height:40px}
.filters button[aria-pressed="true"]{background:var(--brand);border-color:var(--brand);color:#fff}
table.sum{border-collapse:collapse;margin:16px 0;width:100%;max-width:900px;background:var(--card);border-radius:12px;overflow:hidden}
table.sum th,table.sum td{padding:8px 12px;border-bottom:1px solid var(--line);text-align:left} table.sum td.n{text-align:right;font-variant-numeric:tabular-nums}
.ctx{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:8px 0 12px}
.ctx b{color:var(--brand)}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}
@media (max-width:1100px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}} @media (max-width:640px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:6px;min-width:0}
.card.v-approve{border-top:4px solid var(--ok)} .card.v-revise{border-top:4px solid var(--warn)} .card.v-reject{border-top:4px solid var(--bad)}
.card header{display:flex;gap:10px;align-items:center} .card header small{display:block;color:var(--muted);font-size:12px}
.letter{width:30px;height:30px;border-radius:8px;background:var(--brand);color:#fff;display:grid;place-items:center;font-weight:700;flex:none}
.score{font-size:15px} .score b{font-size:22px} .x{font-size:13px;color:var(--muted)}
.verdict{font-size:12px;font-weight:700;padding:2px 8px;border-radius:999px;border:1px solid currentColor;margin-left:4px}
.verdict.approve{color:var(--ok)} .verdict.revise{color:var(--warn)} .verdict.reject{color:var(--bad)}
h4{margin:6px 0 0;font-size:17px} .q{font-weight:600;margin:0} ol{margin:0;padding-left:22px} li.correct{font-weight:700;color:var(--ok)}
.reveal{color:var(--muted);font-size:14px;margin:0}
mark{border-radius:3px;padding:0 2px;color:inherit} mark.major,mark.critical{background:var(--markmaj);text-decoration:underline wavy var(--bad)} mark.minor{background:var(--markmin)}
details{font-size:14px} summary{cursor:pointer;color:var(--brand);font-weight:600;min-height:28px}
.errs{padding-left:18px;margin:6px 0} .errs li{margin:4px 0}
.sev{font-size:11px;font-weight:700;padding:1px 6px;border-radius:6px;border:1px solid currentColor;text-transform:uppercase}
.sev.major,.sev.critical{color:var(--bad)} .sev.minor{color:var(--warn)}
.gloss{color:var(--muted);margin:4px 0}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;color:var(--muted)}
section.moment[hidden]{display:none}
.how{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px 22px;margin:20px 0}
.how h2{margin-top:0} .how h3{font-size:17px;margin:18px 0 8px;color:var(--brand)} .how ul{padding-left:20px;margin:0} .how li{margin:6px 0}
.how a{color:var(--brand)} .links{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px} .links a{font-size:13px;padding:2px 9px;border:1px solid var(--line);border-radius:999px;text-decoration:none;white-space:nowrap} .links a:hover{border-color:var(--brand)} .jump a{display:inline-block;margin:8px 0 4px;padding:10px 16px;border-radius:999px;background:var(--brand);color:#fff;text-decoration:none;font-weight:600} .how{scroll-margin-top:72px}
.steps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px} .step{border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.step p{margin:4px 0 0;color:var(--muted);font-size:15px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:24px}
@media (max-width:900px){.steps{grid-template-columns:1fr 1fr}.cols{grid-template-columns:1fr}} @media (max-width:560px){.steps{grid-template-columns:1fr}} section.moment{scroll-margin-top:72px}
"""


def build():
    by = load()
    # summary per arm
    agg = defaultdict(lambda: {"n": 0, "approve": 0, "major": 0, "score": 0.0})
    for (_, _, _), arms in by.items():
        for k, r in arms.items():
            if r.get("judgement"):
                a = agg[k]
                a["n"] += 1
                a["approve"] += r["judgement"]["verdict"] == "approve"
                a["major"] += sum(e["severity"] != "minor" for e in r["judgement"]["errors"])
                a["score"] += score(r["judgement"])
    sumrows = "".join(
        f'<tr><td><b>{l}</b> {n}</td><td class="n">{agg[k]["approve"]}/{agg[k]["n"]}</td><td class="n">{agg[k]["major"]}</td><td class="n">{agg[k]["score"]/max(1,agg[k]["n"]):.2f}</td></tr>'
        for k, l, n, _ in ARMS
    )
    how_html, how_md = provenance()
    order = sorted(by.keys(), key=lambda k: (k[0], k[1], ["lt", "lv", "et"].index(k[2])))
    sections, md = [], []
    for ev_name, mid, lang in order:
        ev, m = moment_of(ev_name, mid)
        arms = by[(ev_name, mid, lang)]
        cards = "".join(card(arms.get(a[0]), a) for a in ARMS)
        sections.append(
            f'<section class="moment" data-lang="{lang}" data-sport="{ev["sport"]}"><h2>{LANG[lang]}: {html.escape(ev["home"])} vs {html.escape(ev["away"])}</h2>'
            f'<div class="ctx"><b>{html.escape(ev["sport"])}, {html.escape(m["buff_type"])}</b> · {html.escape(m["state"])}<br>{html.escape(m["text"])}</div>'
            f'<div class="grid">{cards}</div></section>'
        )
        md.append(f"### {LANG[lang]}: {ev['home']} vs {ev['away']} ({ev['sport']}, {m['buff_type']})\n\n_{m['state']}. {m['text']}_\n")
        md.append("| | Question and options | Judge | Major errors |\n|---|---|---|---|")
        for k, l, n, _ in ARMS:
            r = arms.get(k)
            if not r or not r.get("buff"):
                md.append(f"| **{l}** {n} | (no result) | | |")
                continue
            b, j = r["buff"], r["judgement"]
            majors = "; ".join(f"{e['category']}: “{e['span']}”" for e in j["errors"] if e["severity"] != "minor") or "none"
            q = (b["question"] + " — " + " / ".join(b["options"])).replace("|", "/").replace(" — ", "<br>")
            md.append(f"| **{l}** {n} | {q} | {score(j)} {j['verdict']} | {majors.replace('|', '/')} |")
        md.append("")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Baltic Buff Examples</title><style>{CSS}</style></head><body><div class="wrap">
<h1>Baltic buff examples: old methods vs the new pipeline</h1>
<p class="lead">The same 18 live moments (3 matches × 2 moments × Lithuanian, Latvian, Estonian), written four ways. All four use the same model, claude-opus-5-5, so the differences come from the method. Scores come from a blind judge that sees only the match facts and the card; highlighted words are what it flagged.</p>
<p class="jump"><a href="#how">How we got these results: data, libraries, models and scoring ↓</a></p>
<table class="sum"><tr><th>Approach</th><th>Approved</th><th>Major + critical errors</th><th>Mean score /5</th></tr>{sumrows}</table>
{how_html}
<div class="legend"><span><mark class="major">major error</mark></span><span><mark class="minor">minor</mark></span><span>Top border: green approved, amber revise, red reject</span></div>
<nav class="filters" aria-label="Filter examples">
<button data-f="all" aria-pressed="true">All</button><button data-f="lt" aria-pressed="false">Lithuanian</button><button data-f="lv" aria-pressed="false">Latvian</button><button data-f="et" aria-pressed="false">Estonian</button>
<button data-f="basketball" aria-pressed="false">Basketball</button><button data-f="ice hockey" aria-pressed="false">Ice hockey</button><button data-f="football" aria-pressed="false">Football</button>
</nav>
{''.join(sections)}
<p class="muted">Sources: {RUN_A.relative_to(ROOT)} (A) and {RUN_R2.relative_to(ROOT)} (B, C, D). Regenerate with python3 -I tools/build_examples.py.</p>
</div>
<script>
document.querySelectorAll('.filters button').forEach(b=>b.addEventListener('click',()=>{{
 document.querySelectorAll('.filters button').forEach(x=>x.setAttribute('aria-pressed',x===b));
 const f=b.dataset.f; document.querySelectorAll('section.moment').forEach(s=>s.hidden=!(f==='all'||s.dataset.lang===f||s.dataset.sport===f));}}));
</script></body></html>"""
    DOCS.mkdir(exist_ok=True)
    (DOCS / "examples.html").write_text(page, encoding="utf-8")
    summary_md = "\n".join(
        f"| **{l}** {n} | {agg[k]['approve']}/{agg[k]['n']} | {agg[k]['major']} | {agg[k]['score']/max(1,agg[k]['n']):.2f} |" for k, l, n, _ in ARMS
    )
    (DOCS / "EXAMPLES.md").write_text(
        "# Examples: every buff, old methods vs the new pipeline\n\n"
        "Generated by `tools/build_examples.py` from real runs. All four approaches use `claude-opus-5-5`, so differences come from the method. "
        "The interactive version with highlighted errors, English meanings and review-team decisions is `docs/examples.html`.\n\n"
        "| Approach | Approved | Major + critical errors | Mean score /5 |\n|---|---|---|---|\n" + summary_md + "\n\n"
        "A: today's Translate button. B: today's `sports_native` prompt. C: native-first pipeline (round 1 design). D: review-team pipeline (round 2).\n\n" + how_md + "\n"
        + "\n".join(md),
        encoding="utf-8",
    )
    print("wrote", DOCS / "examples.html", "and", DOCS / "EXAMPLES.md", len(order), "moments")


if __name__ == "__main__":
    build()
