"""Same data as wikidata_labels.py but via the Action API (wbgetentities), not SPARQL.

Verified 2026-11-17. Preferred for runtime/precompute because WDQS (SPARQL) is frequently
rate-limited (we got HTTP 429 "1 req/min" during a WDQS outage the same day).
Up to 50 ids per call. No key needed.
"""
import json, sys, urllib.parse, urllib.request
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from wikidata_labels import ENTITIES  # noqa: E402

API = "https://www.wikidata.org/w/api.php"
UA = "baltic-buff-lab-poc/0.1 (research script)"
LANGS = ["lt", "lv", "et"]


def fetch(qids):
    params = {"action": "wbgetentities", "ids": "|".join(qids), "format": "json",
              "props": "labels|aliases|sitelinks", "languages": "en|mul|lt|lv|et",
              "sitefilter": "ltwiki|lvwiki|etwiki"}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["entities"]


def localized(ent, lang):
    """Best display name for lang: own label -> own wiki title -> mul label -> en."""
    lab = ent.get("labels", {})
    if lang in lab:
        return lab[lang]["value"], "label"
    sl = ent.get("sitelinks", {}).get(f"{lang}wiki")
    if sl:
        return sl["title"], "wiki"
    if "mul" in lab:
        return lab["mul"]["value"], "mul"
    return lab.get("en", {}).get("value", ""), "en-fallback"


if __name__ == "__main__":
    qids = sys.argv[1:] or list(ENTITIES)
    ents = fetch(qids)
    for q in qids:
        e = ents[q]
        row = {"qid": q, "en": e.get("labels", {}).get("en", {}).get("value")}
        for l in LANGS:
            name, src = localized(e, l)
            row[l] = f"{name} [{src}]"
            row[f"alias_{l}"] = [a["value"] for a in e.get("aliases", {}).get(l, [])]
        print(json.dumps(row, ensure_ascii=False))
