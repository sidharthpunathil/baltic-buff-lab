"""Sports reference layer: resolve real players/teams to Wikidata and pull their localized names.

Why: the model should not invent how "Real Madrid" or "Porziņģis" is written in Latvian. Wikidata
carries editor-curated labels per language (e.g. lv: Madrides "Real", lt: Kauno Žalgiris). Labels
are nominative only, so a second step (inflect.py) builds case tables on top of them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import urllib.parse
import urllib.request

from .config import CACHE, settings

API = "https://www.wikidata.org/w/api.php"


@dataclass
class Entity:
    qid: str
    kind: str  # player | team | competition | venue
    en: str
    labels: dict[str, str | None] = field(default_factory=dict)
    aliases: dict[str, list[str]] = field(default_factory=dict)

    def label(self, lang: str) -> tuple[str, str]:
        """Best nominative label for lang and where it came from."""
        if self.labels.get(lang):
            return self.labels[lang], "wikidata:" + lang
        if self.labels.get("mul"):
            return self.labels["mul"], "wikidata:mul"
        return self.en, "fallback:en"


def _cache_path(name: str):
    CACHE.mkdir(parents=True, exist_ok=True)
    return CACHE / name


def _get(params: dict) -> dict:
    # urllib, not httpx: Wikimedia's bot filter currently 403s httpx's client fingerprint.
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": settings.wikidata_ua})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def resolve(name: str, kind: str, qid: str | None = None) -> Entity:
    """Look up an entity by QID (preferred) or by English search. Cached on disk."""
    key = f"wd_{qid or name}.json".replace("/", "_").replace(" ", "_")
    cp = _cache_path(key)
    if cp.exists():
        d = json.loads(cp.read_text())
        return Entity(**d)
    if not qid:
        hits = _get({"action": "wbsearchentities", "search": name, "language": "en", "limit": 1})["search"]
        if not hits:
            ent = Entity(qid="", kind=kind, en=name)
            cp.write_text(json.dumps(ent.__dict__, ensure_ascii=False))
            return ent
        qid = hits[0]["id"]
    data = _get(
        {"action": "wbgetentities", "ids": qid, "props": "labels|aliases", "languages": "en|mul|lt|lv|et"}
    )["entities"][qid]
    labels = {l: data.get("labels", {}).get(l, {}).get("value") for l in ("en", "mul", "lt", "lv", "et")}
    aliases = {l: [a["value"] for a in data.get("aliases", {}).get(l, [])] for l in ("lt", "lv", "et")}
    ent = Entity(qid=qid, kind=kind, en=labels.get("en") or labels.get("mul") or name, labels=labels, aliases=aliases)
    cp.write_text(json.dumps(ent.__dict__, ensure_ascii=False))
    return ent
