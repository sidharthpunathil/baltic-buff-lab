"""Hunspell spell check for lt/lv/et via spylls (pure Python) using the dictionaries bundled in phunspell.
Verified 2026-11-17: pip install spylls phunspell  (phunspell ships LibreOffice dicts incl. lt_LT, lv_LV, et_EE)
"""
import os, time, phunspell
from spylls.hunspell import Dictionary

DICT_DIR = os.path.join(os.path.dirname(phunspell.__file__), "data", "dictionary")
WORDS = {
    "lt_LT": ["krepšininkas", "krepšinninkas", "rungtynės", "rungtynėse", "įvartį", "įvarti", "Žalgiris", "Messi"],
    "lv_LV": ["futbolists", "futbollists", "vārtsargs", "vartsargs", "spēlē", "Porziņģis", "Mesi"],
    "et_EE": ["jalgpallur", "jalgpalllur", "väravavaht", "väravavahti", "Meistrite", "liiga", "Messi"],
}
for code, words in WORDS.items():
    t = time.time(); d = Dictionary.from_files(os.path.join(DICT_DIR, code, code)); load = time.time() - t
    for w in words:
        ok = d.lookup(w)
        sugg = [] if ok else list(d.suggest(w))[:4]
        print(code, w, ok, sugg)
    print(code, f"load {load:.1f}s")
