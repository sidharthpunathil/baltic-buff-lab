"""Specialist review agents + an orchestrator (arm D).

One generalist judge mixes everything into one pass and, in run 1, produced false positives (it
"corrected" a press-correct Latvian name). Here each reviewer owns one error class, sees only the
reference data it needs, and returns findings with a confidence. The orchestrator (plain code, so
its decisions are auditable) merges them, dismisses findings contradicted by press evidence or by
deterministic checks, decides what blocks publication, routes fixes to the repair step, and on the
next round re-runs only the reviewers whose area changed (plus grammar, since any edit can break
agreement).

The final SCORE still comes from the independent evaluation panel (judge.py), never from this team.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from . import llm, press
from .config import LANG_NAMES, settings
from .inflect import forms_block
from .locale_pack import LocalePack
from .schemas import Buff, EntityForms


class Finding(BaseModel):
    severity: Literal["minor", "major", "critical"]
    span: str = Field(description="Exact text from the card that is wrong.")
    problem: str
    fix: str = Field(description="Replacement text for the span, in the target language.")
    confidence: float = Field(ge=0, le=1, description="How sure you are this is a real error (0-1).")


class Review(BaseModel):
    findings: list[Finding]
    verdict: Literal["pass", "fix"]


@dataclass
class Specialist:
    key: str
    title: str
    model: str
    brief: str
    needs: tuple[str, ...]  # which reference blocks it gets: style, glossary, names, press, facts


def team() -> list[Specialist]:
    claude = settings.gen_model
    gem = settings.native_ear_model
    return [
        Specialist("grammar", "Grammar & morphology reviewer", claude,
                   "Check ONLY morphology and syntax: case government after verbs/prepositions/negation, numeral+noun "
                   "agreement, gender/number agreement (incl. plural-only nouns), the yes/no question particle, verb "
                   "forms and word order. Ignore style and terminology.", ("style",)),
        Specialist("terms", "Sport terminology reviewer", claude,
                   "Check ONLY sport terminology: every sport concept must use the term this country's broadcasters "
                   "use for THIS sport (glossary is authoritative), no calques, no terms borrowed from another sport "
                   "(e.g. football verbs for hockey goals). Ignore grammar.", ("glossary",)),
        Specialist("names", "Names reviewer", claude,
                   "Check ONLY player, team and country names: each must use a form from the NAMES table in the case "
                   "the sentence needs, with the local club convention (quotes or not, declined or not). PRESS-VERIFIED "
                   "forms are correct by definition: never flag them.", ("names", "press")),
        Specialist("native", "Native-ear reviewer", gem,
                   "You are a native speaker who has never seen the English. Flag ONLY what sounds translated, stiff "
                   "or unnatural to a home fan, and wrong register (the brand uses informal singular 'you'). Do not "
                   "flag grammar or terms that are fine.", ("style",)),
        Specialist("facts", "Facts & card-fit reviewer", claude,
                   "Check ONLY facts and the card: every claim must match MATCH CONTEXT (score, who leads, period, "
                   "player roles); options mutually exclusive and parallel; quiz answer actually correct; title <= 35 "
                   "chars; the question answerable now.", ("facts",)),
    ]


SYSTEM = """You are the {title} on a {lang_name} sports desk reviewing a live fan card ("buff") before it is published.
{brief}
Report only real errors in your area, each with the exact span and a {lang_name} fix. Correct text -> empty list
and verdict "pass". Be precise: a false alarm costs a live slot.
{refs}"""


def _refs(sp: Specialist, pack: LocalePack, sport: str, forms: dict[str, EntityForms], qids: list[str]) -> str:
    out = []
    if "style" in sp.needs:
        out.append("HOUSE STYLE:\n" + pack.style)
    if "glossary" in sp.needs:
        out.append("GLOSSARY:\n" + pack.glossary_block(sport))
    if "names" in sp.needs:
        out.append("NAMES (case tables):\n" + (forms_block(forms) or "(none)"))
    if "press" in sp.needs:
        ev = press.evidence_block(pack.lang, qids)
        out.append("PRESS-VERIFIED NAME FORMS (correct, never flag):\n" + (ev or "(none)"))
    return "\n\n".join(out)


def _card(buff: Buff, event: dict, moment: dict, with_facts: bool) -> str:
    d = {"card": {"type": buff.buff_type, "title": buff.title, "question": buff.question, "options": buff.options,
                  "correct_index": buff.correct_index, "reveal": buff.reveal}}
    if with_facts:
        d["match_context"] = {"match": f"{event['home']} vs {event['away']}", "sport": event["sport"],
                              "state": moment["state"], "moment": moment["text"], "facts": event.get("facts", [])}
    else:
        d["sport"] = event["sport"]
    return json.dumps(d, ensure_ascii=False, indent=1)


def run_specialist(sp: Specialist, buff: Buff, event: dict, moment: dict, pack: LocalePack,
                   forms: dict[str, EntityForms], qids: list[str]) -> tuple[Review | None, str]:
    system = SYSTEM.format(title=sp.title, lang_name=LANG_NAMES[pack.lang], brief=sp.brief,
                           refs=_refs(sp, pack, event["sport"], forms, qids))
    user = _card(buff, event, moment, with_facts="facts" in sp.needs)
    for model in sp.model.split("|") + [settings.gen_model]:  # chain, then fall back to Claude
        try:
            return llm.structured(step=f"review.{sp.key}", model=model, system=system, user=user,
                                  schema=Review, effort="low"), model
        except Exception:
            continue
    return None, "failed"


@dataclass
class Decision:
    blocking: list[dict] = field(default_factory=list)
    advisory: list[dict] = field(default_factory=list)
    dismissed: list[dict] = field(default_factory=list)
    ran: dict[str, str] = field(default_factory=dict)  # reviewer -> model actually used

    @property
    def publish(self) -> bool:
        return not self.blocking


def orchestrate(buff: Buff, event: dict, moment: dict, pack: LocalePack, forms: dict[str, EntityForms],
                qids: list[str], only: set[str] | None = None) -> Decision:
    sps = [s for s in team() if only is None or s.key in only]
    dec = Decision()
    with ThreadPoolExecutor(max_workers=len(sps)) as ex:
        futs = {s.key: ex.submit(run_specialist, s, buff, event, moment, pack, forms, qids) for s in sps}
    verified = set()
    for q in qids:
        e = press.entry(pack.lang, q)
        if e:
            verified.update(e["lemma"].replace('"', " ").split())
            verified.update((e.get("cases") or {}).values())
    seen: set[str] = set()
    for key, fut in futs.items():
        review, model = fut.result()
        dec.ran[key] = model
        if review is None:
            continue
        for f in review.findings:
            item = {"reviewer": key, **f.model_dump()}
            span_tokens = {t.strip('„“"«».,?!:') for t in f.span.split()}
            if key != "facts" and span_tokens and span_tokens <= verified:
                item["why"] = "contradicts press-verified name form"
                dec.dismissed.append(item)
            elif f.span.strip() and f.span not in " ".join([buff.title, buff.question, *buff.options, buff.reveal]):
                item["why"] = "span not in card (hallucinated)"
                dec.dismissed.append(item)
            elif f.span.lower() in seen:
                item["why"] = "duplicate of another reviewer"
                dec.dismissed.append(item)
            elif f.severity != "minor" and f.confidence >= 0.6:
                seen.add(f.span.lower())
                dec.blocking.append(item)
            else:
                dec.advisory.append(item)
    return dec


def repair_brief(dec: Decision) -> list[str]:
    """Route fixes grouped by reviewer so the generator knows what kind of change each is."""
    out = []
    for key in ("facts", "names", "terms", "grammar", "native"):
        for f in [b for b in dec.blocking if b["reviewer"] == key]:
            out.append(f"[{key}] '{f['span']}': {f['problem']} -> use: {f['fix']}")
    return out


def rerun_set(dec: Decision) -> set[str]:
    return {b["reviewer"] for b in dec.blocking} | {"grammar"}
