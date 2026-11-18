"""Native-language sports text feeds for few-shot / RAG / glossary mining. Verified 2026-11-17 (HTTP 200, items present).
Stdlib only. Use for headline-style few-shots and to harvest how outlets inflect foreign names.
Respect each outlet's terms; store headlines + links, not full articles, unless licensed.
"""
import re, urllib.request, xml.etree.ElementTree as ET

FEEDS = {
    "lt": [("LRT sportas", "https://www.lrt.lt/tema/sportas?rss", None)],
    "lv": [("LSM (all sections; filter sports)", "https://www.lsm.lv/rss/", "/raksts/sports/"),
           ("Sportacentrs.com", "https://sportacentrs.com/rss", None)],
    "et": [("ERR Sport", "https://sport.err.ee/rss", None)],
}
# Checked and NOT usable from a script on 2026-11-17 (HTTP 403 to non-browser clients):
# 15min.lt/rss/sportas, lrytas.lt/rss/sportas, basketnews.lt/rss, delfi.lv/rss/?channel=sports, sport.delfi.ee/rss
UA = "Mozilla/5.0 (baltic-buff-lab-poc research)"


def fetch(url, must_contain=None, limit=10):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
    out = []
    for it in root.iter("item"):
        title = re.sub(r"\s+", " ", (it.findtext("title") or "")).strip()
        link = (it.findtext("link") or "").strip()
        if must_contain and must_contain not in link:
            continue
        out.append((title, link))
        if len(out) >= limit:
            break
    return out


if __name__ == "__main__":
    for lang, feeds in FEEDS.items():
        for name, url, flt in feeds:
            items = fetch(url, flt, 5)
            print(f"\n[{lang}] {name} ({len(items)} shown)")
            for t, l in items:
                print("  -", t)
