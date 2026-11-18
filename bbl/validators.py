"""Deterministic checks. Cheap, instant, no LLM. They catch the failure classes LLMs repeat:
dropped diacritics, letters from the wrong Baltic alphabet, banned calques, English leakage,
names in forms that don't exist, wrong quote marks, card overflow, broken option sets.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .locale_pack import LocalePack
from .schemas import Buff

TITLE_MAX = 35
QUESTION_MAX = 120
OPTION_MAX = 32

# Letters that exist in one Baltic alphabet but not the others. A Latvian "ā" inside Lithuanian
# copy (or Estonian "õ" in Latvian) means the model blended languages.
ALPHABET_EXTRA = {
    "lt": set("ąčęėįšųūž"),
    "lv": set("āčēģīķļņšūž"),
    "et": set("õäöüšž"),
}
ENGLISH_TELLS = {
    "the", "who", "will", "what", "which", "match", "goal", "score", "team", "player", "next",
    "win", "first", "half", "game", "vote", "and", "or", "of", "is", "best",
}


@dataclass
class Issue:
    code: str
    severity: str  # error | warn
    message: str

    def __str__(self) -> str:
        return f"[{self.severity}] {self.code}: {self.message}"


def _letters(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalpha())


def _words(text: str) -> list[str]:
    return re.findall(r"[\w’'-]+", text, flags=re.UNICODE)


def _stem(word: str) -> str:
    # crude stem good enough to catch inflected calques: drop last 2 letters on longer words
    w = word.lower()
    return w[:-2] if len(w) > 5 else w


def check(buff: Buff, pack: LocalePack, sport: str, name_forms: set[str] | None = None) -> list[Issue]:
    lang = pack.lang
    issues: list[Issue] = []
    texts = [buff.title, buff.question, *buff.options, buff.reveal]
    joined = " ".join(texts)

    # 1. Card fit (UI): JIL renders on small cards.
    if len(buff.title) > TITLE_MAX:
        issues.append(Issue("len.title", "error", f"title {len(buff.title)}>{TITLE_MAX} chars"))
    if len(buff.question) > QUESTION_MAX:
        issues.append(Issue("len.question", "warn", f"question {len(buff.question)}>{QUESTION_MAX} chars"))
    for o in buff.options:
        if len(o) > OPTION_MAX:
            issues.append(Issue("len.option", "warn", f"option '{o}' {len(o)}>{OPTION_MAX} chars"))

    # 2. Option set integrity.
    if not 2 <= len(buff.options) <= 4:
        issues.append(Issue("opt.count", "error", f"{len(buff.options)} options"))
    if len({o.strip().lower() for o in buff.options}) != len(buff.options):
        issues.append(Issue("opt.dupe", "error", "duplicate options"))
    if buff.buff_type == "quiz" and (buff.correct_index is None or not 0 <= buff.correct_index < len(buff.options)):
        issues.append(Issue("opt.answer", "error", "quiz without a valid correct_index"))

    # 3. Orthography: wrong-alphabet letters and stripped diacritics.
    own = ALPHABET_EXTRA[lang]
    foreign = set().union(*(v for k, v in ALPHABET_EXTRA.items() if k != lang)) - own
    proper = name_forms or set()
    for w in _words(joined):
        if w in proper or any(w in p for p in proper):
            continue  # names can legitimately carry foreign letters (e.g. Porziņģis in LT copy)
        bad = {ch for ch in w.lower() if ch in foreign}
        if bad:
            issues.append(Issue("ortho.foreign_letter", "error", f"'{w}' has {''.join(sorted(bad))} (not {lang})"))
    # Partial ASCII-folding ("laimes" for "laimės") is the common failure, so measure density of
    # native diacritics over non-name words; natural lt/lv text sits well above the floor.
    plain = " ".join(w for w in _words(joined) if not any(w in p for p in proper))
    letters = _letters(plain)
    floor = pack.facts.get("min_diacritic_density", 0.035)
    if len(letters) > 40:
        density = sum(ch in own for ch in letters) / len(letters)
        if density < floor:
            issues.append(
                Issue("ortho.no_diacritics", "error", f"diacritic density {density:.1%} < {floor:.0%}: looks ASCII-folded")
            )
    if any(unicodedata.combining(ch) for ch in unicodedata.normalize("NFD", joined)) and joined != unicodedata.normalize("NFC", joined):
        issues.append(Issue("ortho.nfc", "warn", "text is not NFC-normalized"))

    # 4. Typography: quotes and decimal separator.
    bad_quotes = pack.facts.get("bad_quotes", [])
    for q in bad_quotes:
        if q in joined:
            issues.append(Issue("typo.quotes", "warn", f"uses {q!r}; locale prefers {pack.facts.get('quotes')}"))
    if re.search(r"\d\.\d", joined) and pack.facts.get("decimal") == ",":
        issues.append(Issue("typo.decimal", "warn", "decimal point instead of comma"))

    # 5. Terminology: discouraged calques from the glossary (stem match catches inflected forms).
    low = joined.lower()
    for g in pack.glossary_for(sport):
        # Mask every inflected occurrence of the PREFERRED term first, so an avoid-term that is a
        # substring of it ("soda sitiens" inside "11 metru soda sitiens", "pool" inside "poolaeg")
        # isn't reported. Round 2 lost two repair rounds per buff to exactly this.
        masked = low
        for pref in re.split(r"[;/]", g["term"]):
            words = [_stem(w) for w in re.sub(r"\(.*?\)", "", pref).lower().split()]
            if words and all(len(w) >= 2 for w in words):
                masked = re.sub(r"\b" + r"\w*\s+".join(re.escape(w) for w in words) + r"\w*", " ", masked)
        for bad in g.get("avoid", []):
            bad = re.sub(r"\(.*?\)", "", bad).strip()
            st = _stem(bad)
            if len(st) >= 4 and re.search(rf"\b{re.escape(st)}", masked):
                sev = "error" if g.get("verified") else "warn"
                issues.append(Issue("term.calque", sev, f"'{bad}' used; prefer '{g['term']}' for '{g['en']}'"))

    # 5b. Locale rules distilled from research/01 (translationese tells, register, plural-only nouns).
    for rule in pack.facts.get("forbidden_patterns", []):
        m = re.search(rule["pattern"], joined)
        if m and not any(m.group(0) in p for p in proper):
            issues.append(Issue("locale.rule", rule["severity"], f"'{m.group(0)}': {rule['message']}"))

    # 5c. Yes/no buffs need the language's question particle (Ar / Vai / Kas).
    yes = {"taip", "jā", "jah"}
    particle = pack.facts.get("yesno_particle")
    if particle and any(o.split(",")[0].strip().lower() in yes for o in buff.options):
        if not buff.question.strip().startswith(particle):
            issues.append(Issue("grammar.yesno", "warn", f"yes/no question should start with '{particle}'"))

    # 5d. Hunspell: unknown words outside names (folded diacritics, invented inflections).
    try:
        from .spell import unknown_words

        cand = [w for w in _words(joined) if not any(w in p for p in proper) and w[:1].islower()]
        for w, sugg in unknown_words(lang, cand):
            issues.append(Issue("spell.unknown", "warn", f"'{w}' not in {lang} dictionary; suggestions {sugg}"))
    except Exception as exc:  # dictionary missing: don't block the run
        issues.append(Issue("spell.unavailable", "warn", str(exc)[:120]))

    # 6. English leakage.
    leaked = [w for w in _words(joined) if w.lower() in ENGLISH_TELLS and w not in proper]
    if len(leaked) >= 2:
        issues.append(Issue("lang.english", "error", f"English words: {leaked}"))

    # 7. Names: a capitalized token that shares a stem with a known name must be a known form.
    if proper:
        stems = {_stem(p.split()[-1].strip('"„“')) for p in proper if p}
        known = {t for p in proper for t in _words(p)}
        for w in _words(" ".join(texts[:-1])):
            if w[:1].isupper() and w not in known and any(s and w.lower().startswith(s[: max(4, len(s) - 1)]) for s in stems):
                issues.append(Issue("name.form", "warn", f"'{w}' is not in the case table for any entity"))
    return issues


def errors(issues: list[Issue]) -> list[Issue]:
    return [i for i in issues if i.severity == "error"]
