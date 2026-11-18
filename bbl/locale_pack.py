"""Per-language knowledge pack: style guide, glossary, few-shot exemplars, orthography facts.

Everything here is plain files a native linguist can edit without touching code:
  locales/<lang>/style.md       rules (register, quotes, numerals, name handling, translationese tells)
  locales/<lang>/locale.json    machine facts used by validators (alphabet, quotes, decimal sep, ...)
  locales/<lang>/fewshot.json   gold native buffs (approved/edited by natives; the flywheel feeds this)
  data/glossary/<lang>.json     sport terms: preferred term + discouraged calques + source
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache

from .config import DATA, LOCALES


SPORT_ALIASES = {"ice hockey": "hockey", "soccer": "football"}


@dataclass
class LocalePack:
    lang: str
    style: str
    facts: dict
    fewshot: list[dict]
    glossary: list[dict]

    def glossary_for(self, sport: str) -> list[dict]:
        sport = SPORT_ALIASES.get(sport, sport)
        return [g for g in self.glossary if g.get("sport") in (sport, "general", None)]

    def glossary_block(self, sport: str) -> str:
        rows = []
        for g in self.glossary_for(sport):
            avoid = f"  (NOT: {', '.join(g['avoid'])})" if g.get("avoid") else ""
            note = f" [{g['note']}]" if g.get("note") and len(g["note"]) < 160 else ""
            rows.append(f"- {g['en']} = {g['term']}{avoid}{note}")
        return "\n".join(rows) or "(none)"

    def fewshot_block(self, sport: str, k: int = 6) -> str:
        sport = SPORT_ALIASES.get(sport, sport)
        same = [f for f in self.fewshot if f.get("sport") == sport]
        other = [f for f in self.fewshot if f.get("sport") != sport]
        picked = (same + other)[:k]
        return "\n".join(json.dumps(f, ensure_ascii=False) for f in picked) or "(none yet)"


def _read_json(path, default):
    return json.loads(path.read_text()) if path.exists() else default


@lru_cache
def load(lang: str) -> LocalePack:
    d = LOCALES / lang
    return LocalePack(
        lang=lang,
        style=(d / "style.md").read_text() if (d / "style.md").exists() else "",
        facts=_read_json(d / "locale.json", {}),
        fewshot=_read_json(d / "fewshot.json", []),
        glossary=_read_json(DATA / "glossary" / f"{lang}.json", []),
    )
