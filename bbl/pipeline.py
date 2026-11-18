"""Orchestration: run arms A/B/C for each (moment, language), judge all blind, keep a full trace."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from . import generate, inflect, judge, locale_pack, press, reviewers, validators
from .config import settings
from .entities import resolve
from .schemas import Buff, EntityForms, Judgement


@dataclass
class ArmResult:
    arm: str
    lang: str
    moment_id: str
    buff: Buff | None = None
    issues: list[str] = field(default_factory=list)
    judgement: Judgement | None = None
    xjudgement: Judgement | None = None  # cross-family second opinion
    trace: list[dict] = field(default_factory=list)  # every draft/repair round for C/D
    internal: dict | None = None  # C: in-loop judge verdict; D: team decisions (never used for scoring)
    error: str | None = None


def entity_forms(event: dict, lang: str, with_press: bool = False) -> dict[str, EntityForms]:
    out: dict[str, EntityForms] = {}
    for e in event.get("entities", []):
        ent = resolve(e["name"], e["kind"], e.get("qid"))
        f = inflect.forms_for(ent, lang)
        out[e["name"]] = press.apply(lang, ent.qid, f) if with_press else f
    return out


def panel(res: ArmResult, event: dict, moment: dict) -> ArmResult:
    """Independent evaluation, identical for every arm: fresh Claude judge + cross-family judge."""
    if not res.buff:
        return res
    pack = locale_pack.load(res.lang)
    if res.judgement is not None and res.internal is None:
        res.internal = {"loop_judge": res.judgement.model_dump()}
    res.judgement = judge.judge(res.buff, event, moment, pack)
    _xjudge(res, event, moment, pack)
    return res


def run_team(event: dict, moment: dict, lang: str, forms: dict[str, EntityForms]) -> ArmResult:
    """Arm D: press-verified names + specialist review team + orchestrator + routed repair."""
    pack = locale_pack.load(lang)
    names = inflect.all_forms(forms)
    qids = [e.get("qid", "") for e in event.get("entities", [])]
    res = ArmResult("D.team", lang, moment["id"])
    draft = generate.arm_baltic_draft(event, moment, pack, forms)
    only = None
    decisions = []
    for round_no in range(settings.max_repairs + 1):
        buff = draft.buff
        issues = validators.check(buff, pack, event["sport"], names)
        dec = reviewers.orchestrate(buff, event, moment, pack, forms, qids, only=only)
        hard = [str(i) for i in validators.errors(issues)] + [str(i) for i in issues if i.code == "spell.unknown"]
        decisions.append({"round": round_no, "ran": dec.ran, "blocking": dec.blocking, "advisory": dec.advisory,
                          "dismissed": dec.dismissed, "validator": hard})
        res.trace.append({"round": round_no, "buff": buff.model_dump(), "notes": draft.reasoning_notes,
                          "issues": [str(i) for i in issues],
                          "judge": {"verdict": "approve" if dec.publish and not hard else "revise"}})
        res.buff, res.issues = buff, [str(i) for i in issues]
        if (dec.publish and not hard) or round_no == settings.max_repairs:
            break
        draft = generate.arm_baltic_repair(event, moment, pack, forms, buff, hard + reviewers.repair_brief(dec))
        only = reviewers.rerun_set(dec)
    res.internal = {"team_decisions": decisions}
    return res


def run_baltic(event: dict, moment: dict, lang: str, forms: dict[str, EntityForms]) -> ArmResult:
    pack = locale_pack.load(lang)
    names = inflect.all_forms(forms)
    res = ArmResult("C.baltic", lang, moment["id"])
    draft = generate.arm_baltic_draft(event, moment, pack, forms)
    for round_no in range(settings.max_repairs + 1):
        buff = draft.buff
        issues = validators.check(buff, pack, event["sport"], names)
        verdict = judge.judge(buff, event, moment, pack)
        res.trace.append(
            {
                "round": round_no,
                "buff": buff.model_dump(),
                "notes": draft.reasoning_notes,
                "issues": [str(i) for i in issues],
                "judge": verdict.model_dump(),
            }
        )
        blocking = (
            validators.errors(issues)
            + [i for i in issues if i.code == "spell.unknown"]
            + [e for e in verdict.errors if e.severity != "minor"]
        )
        res.buff, res.judgement, res.issues = buff, verdict, [str(i) for i in issues]
        if not blocking or round_no == settings.max_repairs:
            break
        problems = [str(i) for i in validators.errors(issues)] + [
            str(i) for i in issues if i.code == "spell.unknown"
        ] + [
            f"{e.category} ({e.severity}) in '{e.span}': {e.explanation} -> {e.suggested_fix}"
            for e in verdict.errors
            if e.severity != "minor"
        ]
        draft = generate.arm_baltic_repair(event, moment, pack, forms, buff, problems)
    return panel(res, event, moment)


def run_simple(arm: str, fn, event: dict, moment: dict, lang: str, names: set[str]) -> ArmResult:
    pack = locale_pack.load(lang)
    res = ArmResult(arm, lang, moment["id"])
    buff = fn(event, moment, lang)
    res.buff = buff
    res.issues = [str(i) for i in validators.check(buff, pack, event["sport"], names)]
    return panel(res, event, moment)


def run_event(event: dict, langs: list[str], arms: list[str], workers: int = 6) -> list[ArmResult]:
    forms_by_lang = {lang: entity_forms(event, lang) for lang in langs}
    press_forms = {lang: entity_forms(event, lang, with_press=True) for lang in langs} if "D" in arms else {}
    jobs = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for moment in event["moments"]:
            for lang in langs:
                forms = forms_by_lang[lang]
                names = inflect.all_forms(forms)
                if "A" in arms:
                    jobs.append(ex.submit(_safe, "A.translate", lambda m=moment, l=lang, n=names: run_simple("A.translate", generate.arm_translate, event, m, l, n), moment, lang))
                if "B" in arms:
                    jobs.append(ex.submit(_safe, "B.native", lambda m=moment, l=lang, n=names: run_simple("B.native", generate.arm_native, event, m, l, n), moment, lang))
                if "D" in arms:
                    jobs.append(ex.submit(_safe, "D.team", lambda m=moment, l=lang, f=press_forms.get(lang): panel(run_team(event, m, l, f), event, m), moment, lang))
                if "C" in arms:
                    jobs.append(ex.submit(_safe, "C.baltic", lambda m=moment, l=lang, f=forms: run_baltic(event, m, l, f), moment, lang))
        return [j.result() for j in jobs]


def _safe(arm: str, thunk, moment: dict, lang: str) -> ArmResult:
    try:
        return thunk()
    except Exception as exc:  # keep the batch going; the report shows the failure
        return ArmResult(arm, lang, moment["id"], error=f"{type(exc).__name__}: {exc}")


def _xjudge(res: ArmResult, event: dict, moment: dict, pack) -> None:
    if settings.xjudge_model and res.buff:
        try:
            res.xjudgement = judge.judge(res.buff, event, moment, pack, model=settings.xjudge_model)
        except Exception as exc:
            res.issues.append(f"[warn] xjudge.failed: {exc}"[:300])
