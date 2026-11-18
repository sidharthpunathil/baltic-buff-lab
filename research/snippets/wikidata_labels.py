"""Fetch lt/lv/et labels + aliases for sports entities from Wikidata (verified 2026-11-17).

Usage: python3 wikidata_labels.py
No API key needed. Wikidata asks for a descriptive User-Agent.
"""
import json
import sys
import urllib.parse
import urllib.request

ENDPOINT = "https://query.wikidata.org/sparql"
UA = "baltic-buff-lab-poc/0.1 (research script)"

# Q-ids: players, clubs, national teams, competitions
ENTITIES = {
    # players
    "Q615": "Lionel Messi", "Q11571": "Cristiano Ronaldo", "Q21621995": "Kylian Mbappe",
    "Q28967995": "Erling Haaland", "Q1354960": "Mohamed Salah",
    "Q14834367": "Kristaps Porzingis", "Q380018": "Jonas Valanciunas",
    # clubs
    "Q50602": "Manchester City", "Q7156": "FC Barcelona", "Q8682": "Real Madrid",
    "Q1130849": "Liverpool FC", "Q18656": "Manchester United", "Q393357": "BC Zalgiris",
    "Q222861": "FC Flora", "Q995093": "Rigas Futbola skola", "Q19963391": "Riga FC",
    # competitions
    "Q18756": "UEFA Champions League", "Q9448": "Premier League", "Q185982": "EuroLeague",
    "Q308798": "Virsliga",
}

QUERY = """
SELECT ?item ?en ?mul ?lt ?lv ?et ?wLt ?wLv ?wEt
       (GROUP_CONCAT(DISTINCT ?altLt; separator="|") AS ?aliasesLt)
       (GROUP_CONCAT(DISTINCT ?altLv; separator="|") AS ?aliasesLv)
       (GROUP_CONCAT(DISTINCT ?altEt; separator="|") AS ?aliasesEt)
WHERE {
  VALUES ?item { %s }
  OPTIONAL { ?item rdfs:label ?en FILTER(LANG(?en)="en") }
  # Since 2024 Wikidata stores language-independent names under the "mul" code and
  # bots removed identical per-language labels, so an empty lt/et label often just means
  # "same as mul". Always fall back: lt label -> lt Wikipedia title -> mul label.
  OPTIONAL { ?item rdfs:label ?mul FILTER(LANG(?mul)="mul") }
  OPTIONAL { ?item rdfs:label ?lt FILTER(LANG(?lt)="lt") }
  OPTIONAL { ?item rdfs:label ?lv FILTER(LANG(?lv)="lv") }
  OPTIONAL { ?item rdfs:label ?et FILTER(LANG(?et)="et") }
  OPTIONAL { ?a schema:about ?item; schema:isPartOf <https://lt.wikipedia.org/>; schema:name ?wLt }
  OPTIONAL { ?b schema:about ?item; schema:isPartOf <https://lv.wikipedia.org/>; schema:name ?wLv }
  OPTIONAL { ?c schema:about ?item; schema:isPartOf <https://et.wikipedia.org/>; schema:name ?wEt }
  OPTIONAL { ?item skos:altLabel ?altLt FILTER(LANG(?altLt)="lt") }
  OPTIONAL { ?item skos:altLabel ?altLv FILTER(LANG(?altLv)="lv") }
  OPTIONAL { ?item skos:altLabel ?altEt FILTER(LANG(?altEt)="et") }
}
GROUP BY ?item ?en ?mul ?lt ?lv ?et ?wLt ?wLv ?wEt
"""


def run(qids):
    q = QUERY % " ".join(f"wd:{x}" for x in qids)
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": q, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    out = []
    for b in data["results"]["bindings"]:
        g = lambda k: b.get(k, {}).get("value", "")
        out.append({"qid": g("item").rsplit("/", 1)[-1], "en": g("en"), "mul": g("mul"),
                    "lt": g("lt"), "lv": g("lv"), "et": g("et"),
                    "wiki_lt": g("wLt"), "wiki_lv": g("wLv"), "wiki_et": g("wEt"), "alias_lt": g("aliasesLt"), "alias_lv": g("aliasesLv"), "alias_et": g("aliasesEt")})
    return out


if __name__ == "__main__":
    qids = sys.argv[1:] or list(ENTITIES)
    for row in run(qids):
        print(json.dumps(row, ensure_ascii=False))
