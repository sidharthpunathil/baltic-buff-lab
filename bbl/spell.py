"""Hunspell spell check (LibreOffice lt_LT / lv_LV / et_EE dictionaries bundled with phunspell, run by
pure-Python spylls). Catches partial ASCII-folding and invented word forms that a regex can't."""

from __future__ import annotations

import os
from functools import lru_cache

CODES = {"lt": "lt_LT", "lv": "lv_LV", "et": "et_EE"}


@lru_cache
def _dict(lang: str):
    import phunspell
    from spylls.hunspell import Dictionary

    code = CODES[lang]
    return Dictionary.from_files(os.path.join(os.path.dirname(phunspell.__file__), "data", "dictionary", code, code))


def unknown_words(lang: str, words: list[str]) -> list[tuple[str, list[str]]]:
    d = _dict(lang)
    out = []
    for w in words:
        if any(ch.isdigit() for ch in w) or len(w) < 3:
            continue
        if d.lookup(w) or d.lookup(w.lower()):
            continue
        out.append((w, list(d.suggest(w))[:3]))
    return out
