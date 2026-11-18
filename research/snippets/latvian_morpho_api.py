"""Latvian inflection/analysis via the public Tēzaurs morphology service (verified 2026-11-17).

Base URL: https://morpho-api.tezaurs.lv   (no key; version string on / was "2.202604.0")
NOTE: https://api.tezaurs.lv (the *dictionary* API, /openapi) now requires an API key (email api@tezaurs.lv).
      The old-style path https://api.tezaurs.lv/v1/inflections/<word> returns 404.

Endpoints used here (all GET, JSON):
  /inflect_phrase/en/<phrase>?category=person|org|loc   -> {"Nominative": ..., "Genitive": ..., "Dative": ..., "Accusative": ..., "Locative": ...}
  /inflect_people/en/<name>?gender=m|f                  -> per-token paradigm list
  /inflect_general_lvs/en/<lemma>                       -> full paradigm (common nouns etc.)
  /analyze_lvs/en/<word>?guess=false                    -> [] when the word is not in the lexicon (cheap spell/OOV check)
Observed: "Kristaps Porziņģis" -> Dat "Kristapam Porziņģim", Loc "Kristapā Porziņģī";
          "Kristiāns Ronaldu" -> Dat "Kristiānam Ronaldu" (indeclinable surname kept, correct);
          quoted club names are mangled: 'Mančestras "United"' -> 'Mančestru " United "' (strip quotes first, re-add after).
"""
import json, urllib.parse, urllib.request

BASE = "https://morpho-api.tezaurs.lv"


def _get(path, **params):
    url = BASE + path + ("?" + urllib.parse.urlencode(params) if params else "")
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)


def inflect_phrase(phrase, category="person"):
    return _get("/inflect_phrase/en/" + urllib.parse.quote(phrase), category=category)


def is_known_word(word):
    return bool(_get("/analyze_lvs/en/" + urllib.parse.quote(word), guess="false"))


if __name__ == "__main__":
    for p, c in [("Kristaps Porziņģis", "person"), ("Ērlings Hālands", "person"), ("Rīgas Futbola skola", "org")]:
        print(p, json.dumps(inflect_phrase(p, c), ensure_ascii=False))
    print("vārtsargs known:", is_known_word("vārtsargs"), "| vartsargs known:", is_known_word("vartsargs"))
