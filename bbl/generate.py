"""Three arms, so the comparison is fair and reproducible.

A  translate   : today's editor "Translate" button. English buff -> the exact JIL translate prompt
                 (copied verbatim from backend/app/api/viewer_api_routes.py translate_buff_content).
B  native      : today's sports_native pack rules (read live from the backend prompt file), one call,
                 no glossary, no reference names, no exemplars.
C  baltic      : native-first + locale pack (style guide, glossary, gold exemplars) + Wikidata names
                 + inflection tables, followed by validators -> judge -> targeted repair (pipeline.py).
"""

from __future__ import annotations

import json
import re

from . import llm
from .config import LANG_NAMES, ROOT, settings
from .inflect import forms_block
from .locale_pack import LocalePack
from .schemas import Buff, BuffDraft, EnglishBuff, EntityForms

BACKEND_NATIVE_PROMPT = ROOT.parent / "backend/app/prompts/packs/sports_native/feed_buff_gen/system_prompt.txt"

# Verbatim from viewer_api_routes.translate_buff_content (the manual translate button).
JIL_TRANSLATE_SYSTEM = (
    "You translate live-sports fan-engagement card text. Translate the given JSON "
    "fields into the requested language. Keep translations PUNCHY and no longer than "
    "the source where possible (these render on small cards). Preserve numbers, team "
    "names, player names, and emoji as-is. Return ONLY a JSON object with the same "
    'keys: {"title": str, "question": str, "options": [str, ...]} — options must keep '
    "the exact same count and order."
)

BASE_RULES = """You write ONE interactive buff for fans watching a live match.
Buff types: poll (opinion, no right answer), quiz (one factually correct option, set correct_index),
prediction (about what happens next in this match).
Card-sized: title <= 35 characters, question <= 110 characters, 2-4 options of 1-4 words each.
Base every fact on the MATCH CONTEXT. Never invent stats. Return the schema fields only."""


def _event_block(event: dict, moment: dict) -> str:
    return (
        f"MATCH CONTEXT\nSport: {event['sport']}\nCompetition: {event['competition']}\n"
        f"Match: {event['home']} vs {event['away']}\nScore/state: {moment['state']}\n"
        f"Live moment: {moment['text']}\nRequested buff type: {moment['buff_type']}\n"
        f"Facts you may use: {json.dumps(event.get('facts', []), ensure_ascii=False)}"
    )


# ---------------------------------------------------------------- A: translate (today's button)
def arm_translate(event: dict, moment: dict, lang: str) -> Buff:
    en = llm.structured(
        step="A.english",
        model=settings.baseline_model,
        system=BASE_RULES + "\nWrite in English.",
        user=_event_block(event, moment),
        schema=EnglishBuff,
        effort="low",
    ).buff
    payload = json.dumps(
        {"targetLanguage": lang, "title": en.title, "question": en.question, "options": en.options},
        ensure_ascii=False,
    )
    tr = llm.structured(
        step="A.translate",
        model=settings.baseline_model,
        system=JIL_TRANSLATE_SYSTEM
        + "\nAlso fill reveal (translate this: "
        + json.dumps(en.reveal)
        + ") and english_gloss (the English source). Keep buff_type and correct_index.",
        user=payload,
        schema=EnglishBuff,
        effort="low",
    ).buff
    tr.buff_type, tr.correct_index = en.buff_type, en.correct_index
    return tr


# ---------------------------------------------------------------- B: today's native pack
def _native_section() -> str:
    txt = BACKEND_NATIVE_PROMPT.read_text()
    m = re.search(r"NATIVE LANGUAGE OUTPUT.*?(?=\nFAN CHAT language|\Z)", txt, flags=re.S)
    return m.group(0) if m else ""


def arm_native(event: dict, moment: dict, lang: str) -> Buff:
    system = BASE_RULES + "\n\n" + _native_section() + f"\n\nBUFF_LANGUAGES: [{lang}] ({LANG_NAMES[lang]}). Fill english_gloss in English."
    return llm.structured(
        step="B.native",
        model=settings.baseline_model,
        system=system,
        user=_event_block(event, moment),
        schema=BuffDraft,
        effort="low",
    ).buff


# ---------------------------------------------------------------- C: baltic pipeline generator
BALTIC_SYSTEM = """You are a senior {lang_name} sports-desk editor at a Baltic broadcaster (think Go3 / LRT / LSM / ERR).
You write live fan-engagement buffs directly in {lang_name}. You never translate from English and never
think in English sentence patterns. You write how {lang_name} commentators talk to home fans.

{base_rules}

HOUSE STYLE ({lang_name}) — follow strictly:
{style}

SPORT TERMINOLOGY — use exactly these terms (inflect them as grammar requires); never the NOT forms:
{glossary}

NAMES — use only these forms. Pick the case the sentence needs from the table; never leave a name in
the nominative when the grammar needs another case, never invent a spelling:
{names}

GOLD EXAMPLES approved by native editors (match their register, length and grammar, not their content):
{fewshot}

Before answering, in reasoning_notes state which case each name and term takes and why.
Fill english_gloss with a literal English back-gloss for a non-native operator."""


def system_for(pack: LocalePack, sport: str, forms: dict[str, EntityForms]) -> str:
    return BALTIC_SYSTEM.format(
        lang_name=LANG_NAMES[pack.lang],
        base_rules=BASE_RULES,
        style=pack.style or "(none)",
        glossary=pack.glossary_block(sport),
        names=forms_block(forms) or "(no named entities)",
        fewshot=pack.fewshot_block(sport),
    )


def arm_baltic_draft(event: dict, moment: dict, pack: LocalePack, forms: dict[str, EntityForms]) -> BuffDraft:
    return llm.structured(
        step="C.generate",
        model=settings.gen_model,
        system=system_for(pack, event["sport"], forms),
        user=_event_block(event, moment),
        schema=BuffDraft,
        effort=settings.gen_effort,
    )


def arm_baltic_repair(
    event: dict, moment: dict, pack: LocalePack, forms: dict[str, EntityForms], draft: Buff, problems: list[str]
) -> BuffDraft:
    user = (
        _event_block(event, moment)
        + "\n\nYOUR PREVIOUS DRAFT:\n"
        + draft.model_dump_json()
        + "\n\nA native reviewer and automatic checks found these problems. Fix every one, keep what was "
        "right, and re-check case and agreement on every word you change:\n- "
        + "\n- ".join(problems)
    )
    return llm.structured(
        step="C.repair",
        model=settings.gen_model,
        system=system_for(pack, event["sport"], forms),
        user=user,
        schema=BuffDraft,
        effort=settings.gen_effort,
    )
