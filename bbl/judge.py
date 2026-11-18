"""LLM-as-judge, MQM style (the WMT / GEMBA-MQM recipe), blind to which arm produced the buff.

The judge does not see the English source or how the buff was made, only the match facts and the
target-language card, so 'faithful to the English' can't be rewarded, only 'right for local fans'.
"""

from __future__ import annotations

import json

from . import llm, press
from .config import LANG_NAMES, settings
from .locale_pack import LocalePack
from .schemas import Buff, Judgement

JUDGE_SYSTEM = """You are a demanding native {lang_name} linguist and sports-desk chief editor.
You review a short interactive fan card ("buff") that will be shown live to {lang_name}-speaking fans.
Review it like an MQM annotator. List EVERY error with category and severity:
  critical = wrong facts, wrong language, unreadable or offensive
  major    = a native fan notices immediately: wrong case/agreement, wrong or calqued sport term, name in a
             wrong/non-existent form, unnatural word order that reads as translated, missing diacritics
  minor    = stylistic: slightly stiff phrasing, punctuation/quotes, could be punchier
Do not invent errors: correct text gets an empty list. Score 1-5 each:
  grammar (5 = flawless morphology/syntax), naturalness (5 = indistinguishable from a native editor; 1 = obvious
  machine translation), terminology (5 = exactly what local broadcasters say), faithfulness (5 = matches the
  match facts, nothing invented), engagement (5 = a fan wants to tap it now).
verdict: approve only with no major/critical errors. If not approve, give native_rewrite (same buff_type,
same number of options, same meaning, same correct_index) that a {lang_name} editor would publish.

House style reference for this language:
{style}

Glossary reference:
{glossary}

Press-verified name forms (these spellings are what the country's sports press prints; never flag them):
{press}"""


def judge(buff: Buff, event: dict, moment: dict, pack: LocalePack, model: str | None = None) -> Judgement:
    payload = {
        "match": f"{event['home']} vs {event['away']} ({event['competition']}, {event['sport']})",
        "moment": moment["text"],
        "state": moment["state"],
        "facts": event.get("facts", []),
        "card": {
            "type": buff.buff_type,
            "title": buff.title,
            "question": buff.question,
            "options": buff.options,
            "correct_index": buff.correct_index,
            "reveal": buff.reveal,
        },
    }
    return llm.structured(
        step="judge" if not model else "xjudge",
        model=model or settings.judge_model,
        system=JUDGE_SYSTEM.format(
            lang_name=LANG_NAMES[pack.lang], style=pack.style or "(none)", glossary=pack.glossary_block(event["sport"]),
            press=press.evidence_block(pack.lang, [e.get("qid", "") for e in event.get("entities", [])]) or "(none)",
        ),
        user=json.dumps(payload, ensure_ascii=False, indent=1),
        schema=Judgement,
        effort=settings.judge_effort,
    )
