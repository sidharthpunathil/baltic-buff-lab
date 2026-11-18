"""Press-verified name forms (data/names/press.json) layered over the LLM-drafted case tables.

The first run showed two failure modes this fixes:
  * the drafted table was wrong (lt "Merzlikinas" dropped the ļ; et genitive "Merzļikinsi" vs ERR's "Merzlikinse");
  * the judge flagged a correct form as an error (lv "Donnarumma" is what LSM/Delfi actually print).
So press evidence both corrects the table and is shown to reviewers and judges.
"""

from __future__ import annotations

import json
from functools import lru_cache

from .config import DATA
from .schemas import EntityForms


@lru_cache
def _load() -> dict:
    p = DATA / "names" / "press.json"
    return json.loads(p.read_text()) if p.exists() else {}


def entry(lang: str, qid: str) -> dict | None:
    return _load().get(lang, {}).get(qid)


def apply(lang: str, qid: str, forms: EntityForms) -> EntityForms:
    e = entry(lang, qid)
    if not e:
        return forms
    f = forms.model_copy(deep=True)
    for old, new in (e.get("substitute") or {}).items():
        f.lemma = f.lemma.replace(old, new)
        for c in f.forms:
            c.singular = c.singular.replace(old, new)
            c.short = c.short.replace(old, new)
    if e.get("lemma"):
        f.lemma = e["lemma"]
    for c in f.forms:
        pinned = (e.get("cases") or {}).get(c.case)
        if pinned:
            c.short = pinned
    f.usage_note = f"PRESS-VERIFIED: {e['evidence']} | " + f.usage_note
    return f


def evidence_block(lang: str, qids: list[str]) -> str:
    lines = []
    for q in qids:
        e = entry(lang, q)
        if e:
            lines.append(f"- {e['lemma']}: {e['evidence']} (source: {e['sources'][0]})")
    return "\n".join(lines)
