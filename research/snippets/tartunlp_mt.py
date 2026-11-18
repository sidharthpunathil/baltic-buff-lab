"""TartuNLP public MT API (neurotolge.ee backend) - verified 2026-11-17, no key needed.
GET  https://api.tartunlp.ai/translation/v2   -> domains + language pairs (eng/est/lav/lit/ger/fin/rus/ukr + Finno-Ugric)
POST https://api.tartunlp.ai/translation/v2   {"text": "...", "src": "en", "tgt": "et|lv|lt", "domain": "general", "application": "<your app name>"}
Docs: https://api.tartunlp.ai/translation/docs
Observed 2026-11-17 for "Who will score the first goal for Real Madrid tonight?":
  et: "Kes lööb täna õhtul Madridi Reali eest esimese värava?"       (good)
  lt: "Kas šįvakar pasieks pirmąjį \"Real Madrid\" tikslą?"           (WRONG: goal -> 'tikslas' = objective)
  lv: "Kurš šovakar būs pirmais Real Madrid mērķis?"                (WRONG: goal -> 'mērķis' = objective)
=> Useful as an ET back-translation / cross-check signal; do not use as the LT/LV generator.
"""
import json, sys, urllib.request

URL = "https://api.tartunlp.ai/translation/v2"


def translate(text, tgt, src="en"):
    body = json.dumps({"text": text, "src": src, "tgt": tgt, "domain": "general",
                       "application": "baltic-buff-lab-poc"}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["result"]


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or "Who will score the first goal for Real Madrid tonight?"
    for t in ("et", "lv", "lt"):
        print(t, translate(text, t))
