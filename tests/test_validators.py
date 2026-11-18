"""Offline tests for the deterministic layer (no network, no LLM)."""

from bbl.locale_pack import LocalePack
from bbl.schemas import Buff
from bbl.validators import check, errors


def pack(lang, glossary=None, facts=None):
    return LocalePack(lang=lang, style="", facts=facts or {}, fewshot=[], glossary=glossary or [])


def buff(**kw):
    base = dict(
        buff_type="poll",
        title="Kas laimės?",
        question="Kuri komanda laimės trečiąjį kėlinį?",
        options=["Žalgiris", "Real"],
        correct_index=None,
        reveal="Rezultatas paaiškės po kėlinio.",
        english_gloss="Who wins the 3rd quarter?",
    )
    base.update(kw)
    return Buff(**base)


def codes(issues):
    return {i.code for i in issues}


def test_clean_lithuanian_passes():
    assert errors(check(buff(), pack("lt"), "basketball")) == []


def test_ascii_folded_lithuanian_is_flagged():
    b = buff(question="Kuri komanda laimes treciaji kelini po sio taimauto?", reveal="Rezultatas paaiskes po kelinio.")
    assert "ortho.no_diacritics" in codes(check(b, pack("lt"), "basketball"))


def test_latvian_letter_in_lithuanian_is_flagged():
    b = buff(question="Kurā komanda laimės trečiąjį kėlinį?")
    assert "ortho.foreign_letter" in codes(check(b, pack("lt"), "basketball"))


def test_foreign_letters_inside_known_names_are_allowed():
    b = buff(question="Ar Porziņģis pelnys daugiau nei 20 taškų?", options=["Taip", "Ne"])
    issues = check(b, pack("lt"), "basketball", name_forms={"Porziņģis"})
    assert "ortho.foreign_letter" not in codes(issues)


def test_inflected_calque_is_caught_by_stem():
    g = [{"en": "power play", "term": "vairākuma", "avoid": ["spēka spēle"], "sport": "hockey"}]
    b = buff(title="Spēka spēlē!", question="Vai Latvija gūs vārtus spēka spēlē?", options=["Jā", "Nē"],
             reveal="Latvija spēlē vairākumā.")
    assert "term.calque" in codes(check(b, pack("lv", g), "hockey"))


def test_title_overflow_and_dupes():
    b = buff(title="Š" * 40, options=["Taip", "taip"])
    c = codes(check(b, pack("lt"), "basketball"))
    assert {"len.title", "opt.dupe"} <= c


def test_quiz_requires_answer():
    assert "opt.answer" in codes(check(buff(buff_type="quiz"), pack("lt"), "basketball"))


def test_english_leakage():
    b = buff(question="Who will win the trečiąjį kėlinį?")
    assert "lang.english" in codes(check(b, pack("lt"), "basketball"))


def test_decimal_and_quotes_follow_locale():
    b = buff(question='Ar "Žalgiris" pelnys 1.5 karto daugiau?')
    c = codes(check(b, pack("lt", facts={"decimal": ",", "bad_quotes": ['"']}), "basketball"))
    assert {"typo.decimal", "typo.quotes"} <= c


def test_unknown_name_form_is_warned():
    b = buff(question="Ar Franciskus pelnys tritaškį?", options=["Taip", "Ne"])
    issues = check(b, pack("lt"), "basketball", name_forms={"Francisco", "Francisco'ui", "Francisco'u"})
    assert "name.form" in codes(issues)


def test_hunspell_flags_folded_latvian_word():
    b = buff(title="Nākamie vārti", question="Kurš gūs nākamos vartus?", options=["Latvija", "Kanāda"],
             reveal="Spēle turpinās.")
    assert "spell.unknown" in codes(check(b, pack("lv"), "hockey"))


def test_locale_rule_latvian_plural_only_varti():
    import json
    from pathlib import Path
    facts = json.loads(Path("locales/lv/locale.json").read_text())
    b = buff(title="Vārti!", question="Kurš gūs nākamo vārtu?", options=["Latvija", "Kanāda"], reveal="Spēle turpinās.")
    assert "locale.rule" in codes(check(b, pack("lv", facts=facts), "hockey"))


def test_calque_check_ignores_avoid_term_inside_preferred_term():
    import json
    from pathlib import Path
    lv = json.loads(Path("data/glossary/lv.json").read_text())
    et = json.loads(Path("data/glossary/et.json").read_text())
    b = buff(title="Pendele!", question="Vai Igaunija realizēs 11 metru soda sitienu?", options=["Jā", "Nē"],
             reveal="Sitiens precīzs.")
    assert "term.calque" not in codes(check(b, pack("lv", lv), "football"))
    b2 = buff(title="Poolaeg", question="Kes lööb teisel poolajal järgmise värava?", options=["Eesti", "Itaalia"],
              reveal="Selgub poolaja lõpus.")
    assert "term.calque" not in codes(check(b2, pack("et", et), "football"))


def test_calque_check_still_catches_bare_avoid_term():
    import json
    from pathlib import Path
    lv = json.loads(Path("data/glossary/lv.json").read_text())
    rows = [g for g in lv if any("soda sitiens" in a for a in g.get("avoid", []))]
    if rows:  # only meaningful if the glossary lists the bare form as an avoid-term
        b = buff(title="Sods!", question="Vai Igaunija realizēs soda sitienu?", options=["Jā", "Nē"], reveal="Redzēsim.")
        assert "term.calque" in codes(check(b, pack("lv", lv), "football"))
