"""Offline tests: press-verified names and the orchestrator's merge/dismiss rules (no network, no LLM).
The specialist call is replaced by real Review objects fed through the same decision code."""

from bbl import press, reviewers
from bbl.locale_pack import LocalePack
from bbl.schemas import Buff, CaseForm, EntityForms


def table(lemma, short_by_case):
    return EntityForms(lemma=lemma, gender="masculine", declines=True,
                       forms=[CaseForm(case=c, singular=f"X {s}", short=s) for c, s in short_by_case.items()],
                       usage_note="llm draft")


def test_press_fixes_dropped_lithuanian_diacritic():
    f = table("Elvis Merzlikinas", {"vardininkas": "Merzlikinas", "kilmininkas": "Merzlikino", "galininkas": "Merzlikiną"})
    out = press.apply("lt", "Q15238428", f)
    assert out.lemma == "Elvis Merzļikinas"
    assert [c.short for c in out.forms] == ["Merzļikinas", "Merzļikino", "Merzļikiną"]
    assert out.usage_note.startswith("PRESS-VERIFIED")


def test_press_pins_estonian_genitive_from_err():
    f = table("Elvis Merzļikins", {"nimetav": "Merzļikins", "omastav": "Merzļikinsi"})
    out = press.apply("et", "Q15238428", f)
    assert {c.case: c.short for c in out.forms} == {"nimetav": "Merzlikins", "omastav": "Merzlikinse"}


def test_unverified_entity_is_untouched():
    f = table("Karols Metss", {"nominatīvs": "Metss"})
    assert press.apply("lv", "Q12366513", f) == f


def test_evidence_block_lists_sources():
    ev = press.evidence_block("lv", ["Q20830808", "Q-none"])
    assert "Donnarumma" in ev and "delfi.lv" in ev and ev.count("\n") == 0


def _buff():
    return Buff(buff_type="poll", title="Vārti?", question="Vai Latvija iemetīs vārtus pret Donnarummas komandu?",
                options=["Jā", "Nē"], correct_index=None, reveal="Redzēsim.", english_gloss="")


def _decide(monkey_reviews):
    """Run the real orchestrate() with real Review objects per reviewer."""
    orig = reviewers.run_specialist
    reviewers.run_specialist = lambda sp, *a, **k: (monkey_reviews.get(sp.key, reviewers.Review(findings=[], verdict="pass")), "test")
    try:
        pack = LocalePack(lang="lv", style="", facts={}, fewshot=[], glossary=[])
        return reviewers.orchestrate(_buff(), {"sport": "football", "home": "Estonia", "away": "Italy"},
                                     {"state": "", "text": ""}, pack, {}, ["Q20830808"])
    finally:
        reviewers.run_specialist = orig


def F(span, sev="major", conf=0.9):
    return reviewers.Finding(severity=sev, span=span, problem="p", fix="f", confidence=conf)


def test_orchestrator_dismisses_flag_on_press_verified_name():
    d = _decide({"names": reviewers.Review(findings=[F("Donnarummas")], verdict="fix")})
    assert not d.blocking and d.dismissed[0]["why"] == "contradicts press-verified name form"


def test_orchestrator_dismisses_hallucinated_span_and_dupes():
    d = _decide({
        "grammar": reviewers.Review(findings=[F("iemetīs vārtus"), F("not in the card")], verdict="fix"),
        "terms": reviewers.Review(findings=[F("iemetīs vārtus")], verdict="fix"),
    })
    assert [b["reviewer"] for b in d.blocking] == ["grammar"]
    whys = sorted(x["why"] for x in d.dismissed)
    assert whys == ["duplicate of another reviewer", "span not in card (hallucinated)"]


def test_low_confidence_or_minor_is_advisory():
    d = _decide({"native": reviewers.Review(findings=[F("Redzēsim.", "minor"), F("Jā", "major", 0.4)], verdict="fix")})
    assert d.publish and len(d.advisory) == 2


def test_rerun_set_always_includes_grammar():
    d = _decide({"terms": reviewers.Review(findings=[F("iemetīs vārtus")], verdict="fix")})
    assert reviewers.rerun_set(d) == {"terms", "grammar"}
    assert reviewers.repair_brief(d)[0].startswith("[terms] 'iemetīs vārtus'")
