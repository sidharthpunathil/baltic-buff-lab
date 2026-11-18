"""Rule-based Latvian name inflection from the public Tēzaurs morphology service (no key).
Used to overwrite LLM-drafted Latvian case tables with deterministic forms where available."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

BASE = "https://morpho-api.tezaurs.lv"
CASE_MAP = {"Nominative": "nominatīvs", "Genitive": "ģenitīvs", "Dative": "datīvs",
            "Accusative": "akuzatīvs", "Locative": "lokatīvs"}


def inflect_phrase(phrase: str, category: str = "person") -> dict[str, str] | None:
    url = f"{BASE}/inflect_phrase/en/{urllib.parse.quote(phrase)}?category={category}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.load(r)
    except Exception:
        return None
    return {CASE_MAP[k]: v for k, v in data.items() if k in CASE_MAP and isinstance(v, str)} or None
