"""Estonian morphology with EstNLTK/Vabamorf (verified 2026-11-17, estnltk==1.7.5, Python 3.12).

pip install estnltk==1.7.5   # tested in a Python 3.12 venv (a cp312 macOS arm64 wheel exists); license GPL-2.0-only OR Apache-2.0
"""
from estnltk import Text
from estnltk.vabamorf.morf import synthesize, spellcheck, Vabamorf

# 1) Generate case forms. form codes: sg n/g/p/ill/in/el/all/ad/abl/tr/ter/es/ab/kom
CASES = ["sg n", "sg g", "sg p", "sg ill", "sg in", "sg el", "sg all", "sg ad", "sg abl", "sg tr", "sg kom"]
# Observed 2026-11-17:
#  - Pass partofspeech="" for foreign names. With "H", Messi/Ronaldo/Haaland return [] (not in lexicon).
#  - With "": Messi -> Messit/Messiga OK, Ronaldo -> Ronaldot/Ronaldoga OK, Salah -> Salahit/Salahiga OK,
#    but Haaland -> 'haalanut' (guessed as a form of verb 'haalama' - WRONG), Mbappé -> [] (fails),
#    Porziņģis -> gen 'Porziņģisi' (questionable; cf. Žalgiris -> Žalgirise).
#  - Multi-word input ("Meistrite Liiga") returns []; inflect the head word only.
#  => Use Vabamorf to generate candidates + an LLM/human-curated glossary, and always re-analyse the
#     final text (Text(...).tag_layer) to confirm each name form maps back to the intended lemma.
for lemma in ["Messi", "Ronaldo", "Haaland", "Mbappé", "Flora", "Žalgiris", "väravavaht"]:
    forms = {c: synthesize(lemma, c, "") for c in CASES}
    print(lemma, forms)

# 2) Built-in Vabamorf speller (no hunspell needed)
for r in spellcheck(["jalgpallur", "jalgpalllur", "väravavahti", "Messit", "Meistrite"]):
    print(r)

# 3) Full pipeline tagging on a sentence (for agreement checks)
t = Text("Kas Messi lööb täna Floraga mängus kaks väravat?").tag_layer(["morph_analysis"])
for w in t.morph_analysis:
    print(w.text, w.lemma, w.partofspeech, w.form)
