"""Buff Lab Live: a web server that runs the real bbl pipeline and streams every step.

Nothing in bbl/ is changed. The server wraps a handful of module functions (the LLM call, the
generator, validators, reviewers, orchestrator, judge) so each call also emits an event to the
browser: the exact system prompt and user message, the parsed output, tokens, cost and time.

Run from baltic-buff-lab/:
    uv run --with fastapi --with uvicorn uvicorn app.server:app --port 8765
"""

from __future__ import annotations

import contextvars
import json
import os
import queue
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Live defaults, set before bbl reads its settings. The native-ear reviewer runs on Claude and the
# cross-family judge is off, because Gemini overloads made single reviews take minutes.
os.environ.setdefault("BBL_NATIVE_EAR_MODEL", "claude-opus-5-5")
os.environ["BBL_XJUDGE_MODEL"] = os.environ.get("BBL_LIVE_XJUDGE_MODEL", "")

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.responses import FileResponse, StreamingResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from bbl import generate, inflect, judge, llm, locale_pack, pipeline, press, reviewers, validators  # noqa: E402
from bbl.config import LANG_NAMES, ROOT, settings  # noqa: E402
from bbl.entities import resolve  # noqa: E402
from bbl.schemas import Buff  # noqa: E402

EVENTS = ROOT / "samples" / "events"
WEB_DIST = Path(__file__).parent / "web" / "dist"

# $ per token: input, output. Cache writes cost 1.25x input, cache reads 0.05x input.
PRICES = {"claude-opus-5-5": (4e-6, 20e-6), "claude-sonnet-5-5": (2e-6, 10e-6)}

ARMS = {
    "A": {"key": "A", "name": "Today: Translate button", "kind": "old",
          "how": "Writes the buff in English, then runs JIL's Translate prompt on it.",
          "model": settings.baseline_model},
    "B": {"key": "B", "name": "Today: sports_native prompt", "kind": "old",
          "how": "One call with today's native-language rules. No glossary, no name forms, no examples, no checks.",
          "model": settings.baseline_model},
    "C": {"key": "C", "name": "New: native-first", "kind": "new",
          "how": "Locale pack and case tables in the prompt, then validators and a judge that sends fixes back.",
          "model": settings.gen_model},
    "D": {"key": "D", "name": "New: review team", "kind": "new",
          "how": "C plus press-verified names and five specialist reviewers run by a plain-code orchestrator.",
          "model": settings.gen_model},
}

# ------------------------------------------------------------------ instrumentation

CUR: contextvars.ContextVar[dict | None] = contextvars.ContextVar("bbl_live_cur", default=None)
_USAGE: contextvars.ContextVar[dict | None] = contextvars.ContextVar("bbl_live_usage", default=None)


def emit(t: str, **kw) -> None:
    c = CUR.get()
    if c:
        c["emit"]({"t": t, "arm": c["arm"], "round": c["round"], "ts": round(time.monotonic() - c["t0"], 3), **kw})


def cost(model: str, u: dict | None) -> float:
    if not u:
        return 0.0
    pin, pout = PRICES.get(model, PRICES["claude-opus-5-5"])
    return round(u["input"] * pin + u["cache_write"] * pin * 1.25 + u["cache_read"] * pin * 0.05 + u["output"] * pout, 5)


class CtxPool(ThreadPoolExecutor):
    """ThreadPoolExecutor that carries the caller's context, so reviewer threads know their arm."""

    def submit(self, fn, /, *args, **kwargs):
        ctx = contextvars.copy_context()
        return super().submit(ctx.run, fn, *args, **kwargs)


reviewers.ThreadPoolExecutor = CtxPool
pipeline.ThreadPoolExecutor = CtxPool

_orig_client = llm.client


class _Messages:
    def __init__(self, real):
        self._real = real

    def parse(self, **kw):
        resp = self._real.parse(**kw)
        u = resp.usage
        _USAGE.set({
            "input": u.input_tokens or 0,
            "output": u.output_tokens or 0,
            "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0,
            "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0,
            "served_model": getattr(resp, "model", None),
        })
        return resp


class _Client:
    def __init__(self, real):
        self.messages = _Messages(real.messages)


llm.client = lambda: _Client(_orig_client())
_orig_structured = llm.structured


def _structured(*, step, model, system, user, schema, effort="medium", max_tokens=16000):
    if "|" in model:  # the chain re-enters this function once per model it tries
        return _orig_structured(step=step, model=model, system=system, user=user, schema=schema,
                                effort=effort, max_tokens=max_tokens)
    cid = uuid.uuid4().hex[:8]
    emit("llm.start", id=cid, step=step, model=model, effort=effort, schema=schema.__name__,
         system=system, user=user, role=(CUR.get() or {}).get("role"))
    _USAGE.set(None)
    t0 = time.monotonic()
    try:
        out = _orig_structured(step=step, model=model, system=system, user=user, schema=schema,
                               effort=effort, max_tokens=max_tokens)
    except Exception as exc:
        emit("llm.error", id=cid, step=step, seconds=round(time.monotonic() - t0, 2), error=f"{type(exc).__name__}: {exc}"[:400])
        raise
    u = _USAGE.get()
    emit("llm.done", id=cid, step=step, model=model, seconds=round(time.monotonic() - t0, 2), usage=u,
         cost=cost(model, u), output=out.model_dump())
    return out


llm.structured = _structured


def _wrap(module, name, before=None, after=None):
    orig = getattr(module, name)

    def wrapped(*a, **kw):
        if before:
            before(*a, **kw)
        res = orig(*a, **kw)
        if after:
            after(res, *a, **kw)
        return res

    setattr(module, name, wrapped)
    return orig


def _buff_event(draft, *a, **kw):
    emit("buff", buff=draft.buff.model_dump(), notes=draft.reasoning_notes)


def _next_round(*a, **kw):
    c = CUR.get()
    if c:
        c["round"] += 1
    problems = a[5] if len(a) > 5 else kw.get("problems", [])
    emit("repair", problems=list(problems))


_wrap(generate, "arm_baltic_draft", after=_buff_event)
_wrap(generate, "arm_baltic_repair", before=_next_round, after=_buff_event)
_wrap(validators, "check", after=lambda issues, *a, **kw: emit(
    "validators", issues=[{"code": i.code, "severity": i.severity, "message": i.message} for i in issues]))

_orig_run_specialist = reviewers.run_specialist


def _run_specialist(sp, *a, **kw):
    emit("reviewer.start", key=sp.key, title=sp.title, model=sp.model)
    t0 = time.monotonic()
    review, model = _orig_run_specialist(sp, *a, **kw)
    emit("reviewer.done", key=sp.key, model=model, seconds=round(time.monotonic() - t0, 2),
         findings=[f.model_dump() for f in review.findings] if review else None,
         verdict=review.verdict if review else "failed")
    return review, model


reviewers.run_specialist = _run_specialist
_wrap(reviewers, "orchestrate", after=lambda dec, *a, **kw: emit(
    "decision", blocking=dec.blocking, advisory=dec.advisory, dismissed=dec.dismissed, ran=dec.ran, publish=dec.publish))

_orig_judge = judge.judge


def _judge(buff, event, moment, pack, model=None):
    c = CUR.get() or {}
    if c.get("role") == "panel" and not c.get("judge_on", True):
        raise _SkipJudge
    j = _orig_judge(buff, event, moment, pack, model=model)
    emit("judge", role=c.get("role") or "loop", judgement=j.model_dump(), penalty=j.mqm_penalty, mean=j.mean_score)
    return j


class _SkipJudge(Exception):
    pass


judge.judge = _judge
_orig_panel = pipeline.panel


def _panel(res, event, moment):
    c = CUR.get()
    if c:
        c["role"] = "panel"
    try:
        return _orig_panel(res, event, moment)
    except _SkipJudge:
        return res


pipeline.panel = _panel

# ------------------------------------------------------------------ data helpers


def load_event(event_id: str) -> dict:
    for p in EVENTS.glob("*.json"):
        e = json.loads(p.read_text())
        if e["id"] == event_id:
            return e
    raise HTTPException(404, f"no event {event_id}")


def forms_for(event: dict, lang: str, with_press: bool):
    return pipeline.entity_forms(event, lang, with_press=with_press)


def prompt_sections(event: dict, moment: dict, lang: str, forms) -> dict:
    pack = locale_pack.load(lang)
    sport = event["sport"]
    system = generate.system_for(pack, sport, forms)
    parts = [
        ("style", "House style sheet", pack.style or "(none)"),
        ("glossary", "Sport glossary (this sport + general)", pack.glossary_block(sport)),
        ("names", "Name case tables", inflect.forms_block(forms) or "(no named entities)"),
        ("fewshot", "Example buffs", pack.fewshot_block(sport)),
        ("rules", "Card rules", generate.BASE_RULES),
    ]
    sections = [{"key": k, "label": label, "text": txt, "chars": len(txt)} for k, label, txt in parts]
    other = len(system) - sum(s["chars"] for s in sections)
    sections.insert(0, {"key": "role", "label": "Role and instructions", "text": "", "chars": max(other, 0)})
    return {"system": system, "user": generate._event_block(event, moment), "sections": sections}


VALIDATOR_RULES = [
    ("len.title", "error", "Title over 35 characters"),
    ("len.question / len.option", "warn", "Question over 120 or an option over 32 characters"),
    ("opt.count / opt.dupe / opt.answer", "error", "Wrong option count, duplicates, or a quiz without a valid answer"),
    ("ortho.foreign_letter", "error", "A letter from another Baltic alphabet (names exempt)"),
    ("ortho.no_diacritics", "error", "Too few accented letters: the text was probably ASCII-folded"),
    ("spell.unknown", "warn, sent to repair", "A word missing from the Hunspell dictionary"),
    ("term.calque", "error if verified", "A glossary 'avoid' term, matched by stem"),
    ("locale.rule", "per rule", "Regex rules from locale.json"),
    ("grammar.yesno", "warn", "A yes/no question without its particle"),
    ("lang.english", "error", "Two or more English words outside names"),
    ("name.form", "warn", "A capitalised word close to a known name but not in its case table"),
    ("typo.quotes / typo.decimal", "warn", "Wrong quote marks, decimal point instead of comma"),
]

ORCHESTRATOR_RULES = [
    "Dismiss a finding if its span is only press-verified name forms.",
    "Dismiss it if the span doesn't appear on the card (a hallucinated span).",
    "Dismiss it if another reviewer already reported the same span.",
    "Block if it is major or critical with confidence of 0.6 or more.",
    "Otherwise keep it as advisory.",
    "If anything blocks: group fixes by reviewer (facts, names, terms, grammar, native) and send them to repair.",
    f"Next round re-runs only the reviewers that blocked, plus grammar. At most {settings.max_repairs} repairs.",
]

# ------------------------------------------------------------------ API

app = FastAPI(title="Buff Lab Live")


@app.get("/api/meta")
def meta():
    events = []
    for p in sorted(EVENTS.glob("*.json")):
        e = json.loads(p.read_text())
        events.append({k: e[k] for k in ("id", "sport", "competition", "home", "away", "moments", "facts", "entities")})
    return {"events": events, "arms": list(ARMS.values()), "langs": {k: LANG_NAMES[k] for k in ("lt", "lv", "et")},
            "settings": {"gen_model": settings.gen_model, "baseline_model": settings.baseline_model,
                         "judge_model": settings.judge_model, "native_ear_model": settings.native_ear_model,
                         "max_repairs": settings.max_repairs, "gen_effort": settings.gen_effort,
                         "judge_effort": settings.judge_effort}}


@app.get("/api/explore")
def explore(event_id: str, lang: str, moment_id: str | None = None):
    event = load_event(event_id)
    moment = next((m for m in event["moments"] if m["id"] == moment_id), event["moments"][0])
    pack = locale_pack.load(lang)
    sport = event["sport"]
    raw = forms_for(event, lang, with_press=False)
    pressed = forms_for(event, lang, with_press=True)
    entities = []
    for e in event.get("entities", []):
        ent = resolve(e["name"], e["kind"], e.get("qid"))
        label, src = ent.label(lang)
        entities.append({
            "name": e["name"], "kind": e["kind"], "qid": ent.qid, "labels": ent.labels,
            "aliases": ent.aliases.get(lang, []), "label": label, "label_source": src,
            "forms": raw[e["name"]].model_dump(), "forms_press": pressed[e["name"]].model_dump(),
            "press": press.entry(lang, ent.qid), "tezaurs": "Tēzaurs" in raw[e["name"]].usage_note,
        })
    fewshot_picked = pack.fewshot_block(sport).splitlines()
    native_section = generate._native_section()
    b_system = generate.BASE_RULES + "\n\n" + native_section + f"\n\nBUFF_LANGUAGES: [{lang}] ({LANG_NAMES[lang]}). Fill english_gloss in English."
    qids = [e.get("qid", "") for e in event.get("entities", [])]
    team = []
    for sp in reviewers.team():
        system = reviewers.SYSTEM.format(title=sp.title, lang_name=LANG_NAMES[lang], brief=sp.brief,
                                         refs=reviewers._refs(sp, pack, sport, pressed, qids))
        team.append({"key": sp.key, "title": sp.title, "model": sp.model, "brief": sp.brief,
                     "needs": list(sp.needs), "system": system, "chars": len(system)})
    return {
        "entities": entities,
        "pack": {
            "style": pack.style, "facts": pack.facts,
            "glossary": pack.glossary_for(sport), "glossary_total": len(pack.glossary),
            "fewshot": pack.fewshot, "fewshot_picked": len(fewshot_picked),
        },
        "prompt_d": prompt_sections(event, moment, lang, pressed),
        "prompt_c": prompt_sections(event, moment, lang, raw),
        "prompt_a": {"english_system": generate.BASE_RULES + "\nWrite in English.",
                     "translate_system": generate.JIL_TRANSLATE_SYSTEM,
                     "user": generate._event_block(event, moment)},
        "prompt_b": {"system": b_system, "user": generate._event_block(event, moment),
                     "source": str(generate.BACKEND_NATIVE_PROMPT.relative_to(ROOT.parent))},
        "schema": Buff.model_json_schema(),
        "reviewers": team,
        "validator_rules": [{"code": c, "severity": s, "what": w} for c, s, w in VALIDATOR_RULES],
        "orchestrator_rules": ORCHESTRATOR_RULES,
        "settings": {"max_repairs": settings.max_repairs},
    }


class ValidateBody(BaseModel):
    event_id: str
    lang: str
    buff: dict


@app.post("/api/validate")
def validate(body: ValidateBody):
    event = load_event(body.event_id)
    pack = locale_pack.load(body.lang)
    names = inflect.all_forms(forms_for(event, body.lang, with_press=True))
    b = {"buff_type": "poll", "correct_index": None, "reveal": "", "english_gloss": "", **body.buff}
    t0 = time.perf_counter()
    issues = validators.check(Buff.model_validate(b), pack, event["sport"], names)
    return {"ms": round((time.perf_counter() - t0) * 1000, 1),
            "issues": [{"code": i.code, "severity": i.severity, "message": i.message} for i in issues]}


class RunBody(BaseModel):
    event_id: str
    lang: str
    moment: dict  # {id?, buff_type, state, text}
    arms: list[str]
    judge: bool = True


def _run_arm(arm: str, event: dict, moment: dict, lang: str, forms_raw, forms_press, judge_on: bool) -> dict:
    pack = locale_pack.load(lang)
    names = inflect.all_forms(forms_raw)
    if arm in ("A", "B"):
        fn = generate.arm_translate if arm == "A" else generate.arm_native
        buff = fn(event, moment, lang)
        emit("buff", buff=buff.model_dump(), notes=None)
        validators.check(buff, pack, event["sport"], names)
        if judge_on:
            CUR.get()["role"] = "panel"
            judge.judge(buff, event, moment, pack)
        return {"buff": buff.model_dump()}
    if arm == "C":
        emit("context", **prompt_sections(event, moment, lang, forms_raw))
        res = pipeline.run_baltic(event, moment, lang, forms_raw)
        return {"buff": res.buff.model_dump() if res.buff else None}
    emit("context", **prompt_sections(event, moment, lang, forms_press))
    res = pipeline.run_team(event, moment, lang, forms_press)
    if judge_on and res.buff:
        CUR.get()["role"] = "panel"
        judge.judge(res.buff, event, moment, pack)
    return {"buff": res.buff.model_dump() if res.buff else None}


@app.post("/api/run")
def run(body: RunBody):
    event = load_event(body.event_id)
    base = next((m for m in event["moments"] if m["id"] == body.moment.get("id")), {})
    moment = {**base, **{k: v for k, v in body.moment.items() if v}, "id": body.moment.get("id") or "custom"}
    arms = [a for a in body.arms if a in ARMS]
    q: queue.Queue = queue.Queue()
    t0 = time.monotonic()

    def put(ev: dict) -> None:
        q.put(ev)

    def worker():
        try:
            put({"t": "prep.start", "ts": 0})
            tp = time.monotonic()
            forms_raw = forms_for(event, body.lang, with_press=False)
            forms_press = forms_for(event, body.lang, with_press=True)
            put({"t": "prep.done", "ts": round(time.monotonic() - t0, 3), "seconds": round(time.monotonic() - tp, 2),
                 "entities": len(forms_raw)})
            threads = []
            for arm in arms:
                def go(arm=arm):
                    CUR.set({"emit": put, "arm": arm, "round": 0, "t0": t0, "role": None, "judge_on": body.judge})
                    start = time.monotonic()
                    emit("arm.start", meta=ARMS[arm])
                    try:
                        out = _run_arm(arm, event, moment, body.lang, forms_raw, forms_press, body.judge)
                        emit("arm.done", seconds=round(time.monotonic() - start, 2), **out)
                    except Exception as exc:
                        emit("arm.error", seconds=round(time.monotonic() - start, 2), error=f"{type(exc).__name__}: {exc}"[:500])
                th = threading.Thread(target=contextvars.copy_context().run, args=(go,), daemon=True)
                th.start()
                threads.append(th)
            for th in threads:
                th.join()
        except Exception as exc:
            put({"t": "fatal", "error": f"{type(exc).__name__}: {exc}"[:500]})
        finally:
            put({"t": "done", "ts": round(time.monotonic() - t0, 3)})
            q.put(None)

    threading.Thread(target=worker, daemon=True).start()

    def stream():
        yield json.dumps({"t": "run.start", "moment": moment, "lang": body.lang, "arms": arms}) + "\n"
        while (ev := q.get()) is not None:
            yield json.dumps(ev, ensure_ascii=False, default=str) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        return FileResponse(WEB_DIST / "index.html")
