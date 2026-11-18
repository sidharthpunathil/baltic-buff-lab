"""Inflection tables for proper names (the language-learning-app trick).

Duolingo-style apps never let free text decide a word form: they store a lemma plus its paradigm and
pick the form by grammatical slot. We do the same for players/teams: build each name's case table
once per language (LLM drafts it, cache it, a native can correct the JSON file), then
  * the generator is told the exact forms to use, and
  * the validator flags any name spelling that is not in the table.

For Latvian an optional rule-based source exists (Tezaurs.lv); see research/02 for endpoints.
"""

from __future__ import annotations

import json

from . import llm
from .config import CACHE, LANG_NAMES, settings
from .entities import Entity
from .schemas import EntityForms

CASES = {
    "lt": ["vardininkas", "kilmininkas", "naudininkas", "galininkas", "įnagininkas", "vietininkas", "šauksmininkas"],
    "lv": ["nominatīvs", "ģenitīvs", "datīvs", "akuzatīvs", "lokatīvs", "vokatīvs"],
    "et": ["nimetav", "omastav", "osastav", "sisseütlev", "seesütlev", "seestütlev", "alaleütlev",
           "alalütlev", "alaltütlev", "saav", "rajav", "olev", "ilmaütlev", "kaasaütlev"],
}

SYSTEM = """You are a {lang_name} sports-desk copy editor and morphology expert.
Given a sports entity and its curated nominative label, return how {lang_name} sports media write it in
every grammatical case. Follow current official norms ({authority}) and real sports-press usage:
- Lithuanian (15min/LRT practice): consonant-final foreign names get Lithuanian endings on the original
  spelling (Erlingas Haalandas, Haalando); vowel-final names stay UNdeclined (Messi, Ronaldo, Mbappe);
  a silent final letter takes an apostrophe (Kane'ui). First names are adapted (Lionelis Messi).
  Foreign CLUBS: in „…“ quotes and undeclined („Real“); Lithuanian clubs declined inside quotes with
  the city in genitive (Kauno „Žalgiris“, „Žalgirio“). Countries decline normally.
- Latvian (LSM/sportacentrs): foreign personal names are RESPELLED phonetically with Latvian endings
  (Lionels Mesi, Krištianu Ronaldu, Mbapē); -i/-u/-ē final names stay undeclined. CLUBS in "…" quotes,
  undeclined, city in genitive before (Madrides "Real", Kauņas "Žalgiris"). Countries decline.
- Estonian (EKI/ERR): original spelling + case endings by pronunciation, apostrophe ONLY when spelling
  and pronunciation conflict (Messist, Ronaldost; Jane'il). CLUBS have no quotes and decline like nouns,
  with Estonianized city (Madridi Real, Reali vastu; Kaunase Žalgiris). Countries decline.
Players: sports copy mostly uses the surname alone (or initial + surname in LT/LV press), so give the
surname-only form per case in `short`; for teams give the short club/country name per case.
If the entity does not decline in practice, set declines=false and repeat the lemma. Do not decline
what the norm leaves undeclined (e.g. many vowel-final foreign names in Lithuanian).
Return all of these cases in order: {cases}."""

AUTHORITY = {"lt": "VLKK, vlkk.lt", "lv": "VVC / tezaurs.lv", "et": "EKI, ÕS / sonaveeb.ee"}


def forms_for(entity: Entity, lang: str) -> EntityForms:
    cp = CACHE / f"forms_{lang}_{entity.qid or entity.en}.json".replace(" ", "_")
    if cp.exists():
        return EntityForms.model_validate_json(cp.read_text())
    label, src = entity.label(lang)
    user = (
        f"Entity kind: {entity.kind}\nEnglish name: {entity.en}\n"
        f"Curated {LANG_NAMES[lang]} label ({src}): {label}\n"
        f"Known {LANG_NAMES[lang]} aliases: {entity.aliases.get(lang) or []}\n"
        "Build the case table."
    )
    forms = llm.structured(
        step="inflect",
        model=settings.gen_model,
        system=SYSTEM.format(
            lang_name=LANG_NAMES[lang], authority=AUTHORITY[lang], cases=", ".join(CASES[lang])
        ),
        user=user,
        schema=EntityForms,
        effort="medium",
    )
    if lang == "lv" and entity.kind == "player":
        forms = _tezaurs_override(forms)
    cp.write_text(forms.model_dump_json(indent=2))
    return forms


def _tezaurs_override(forms: EntityForms) -> EntityForms:
    """Replace LLM case forms with Tēzaurs morphology output where the service knows the name."""
    from . import tezaurs

    full = tezaurs.inflect_phrase(forms.lemma, "person")
    short = tezaurs.inflect_phrase(forms.lemma.split()[-1], "person")
    if not full:
        return forms
    changed = []
    for c in forms.forms:
        if c.case in full and full[c.case] != c.singular:
            changed.append(f"{c.case}: {c.singular}->{full[c.case]}")
            c.singular = full[c.case]
        if short and c.case in short and short[c.case] != c.short:
            c.short = short[c.case]
    forms.usage_note += " | Tēzaurs morpho-api applied" + (f" ({'; '.join(changed)})" if changed else " (agreed)")
    return forms


def forms_block(entity_forms: dict[str, EntityForms]) -> str:
    """Render the tables for the generator prompt."""
    lines = []
    for en, f in entity_forms.items():
        cases = "; ".join(f"{c.case}: {c.singular} / short: {c.short}" for c in f.forms)
        lines.append(f"- {en} → {f.lemma} ({f.gender}, declines={f.declines}). {cases}. Note: {f.usage_note}")
    return "\n".join(lines)


def all_forms(entity_forms: dict[str, EntityForms]) -> set[str]:
    out: set[str] = set()
    for f in entity_forms.values():
        out.add(f.lemma)
        out.update(c.singular for c in f.forms)
        out.update(c.short for c in f.forms)
    return out


def dump(entity_forms: dict[str, EntityForms]) -> str:
    return json.dumps({k: v.model_dump() for k, v in entity_forms.items()}, ensure_ascii=False, indent=2)
