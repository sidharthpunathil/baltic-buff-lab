# Baltic buffs: tools, models and data (lt / lv / et)

Research date: 2026-11-17. Everything marked "verified" was called or installed on that date from a macOS arm64 machine. Runnable code is in `research/snippets/` (see its README). Anything not marked verified comes from documentation or papers and is cited.

## 0. Claims from the other LLM, checked

| Claim | Verdict | Evidence |
|---|---|---|
| TildeOpen LLM is 30B, open weights, CC-BY-4.0, strong Baltic coverage | Mostly true, with two caveats | HF API: `TildeAI/TildeOpen-30b`, `license: cc-by-4.0`, languages include lt/lv/et (https://huggingface.co/TildeAI/TildeOpen-30b). Paper: arXiv 2603.08182. Caveat 1: it is a base (foundation) model; Tilde has not published an instruct/chat version (their HF org on test day had `TildeOpen-30b`, `TildeOpen-30b-64k` and some WMT26 compression-task checkpoints). A community SFT exists (`martinsu/tildeopen-30b-mu-instruct`). Caveat 2: "strong" is Tilde's own claim (Belebele avg 84.7%, "up to tenfold reduction in linguistic errors" in their human eval). On EuroEval Latvian it ranks #119 of 217 because a base model does poorly on instruction-style tasks; it has no complete LT/ET score. |
| Gemma 2 27B was best open-weight in a 2025 NoDaLiDa/Baltic-HLT paper, COMET near GPT-4o/DeepL | True, but dated | Kapočiūtė-Dzikienė, Bergmanis, Pinnis, "Localizing AI: Evaluating Open-Weight Language Models for Languages of Baltic States", NoDaLiDa/Baltic-HLT 2025 (https://aclanthology.org/2025.nodalida-1.30.pdf). FLORES-200, wmt22-comet-da. EN→LT: DeepL 0.92, GPT-4o 0.91, Gemma 2 27B 0.89. EN→LV: 0.92 / 0.91 / 0.88. EN→ET: 0.93 / 0.92 / 0.89. Human error rate in free-form LT generation: GPT-4o 3.44%, Gemma 2 27B 4.08%, Llama 3.1 70B 7.67%, Neurotechnology LT-Llama-2 13B 0.98%. LV: GPT-4o 2.48%, Gemma 2 27B 5.98%. The models tested are from 2024; Gemma 3/4 and newer closed models have since moved ahead (see section 3). |
| Tezaurs.lv has a morphology API | True, but the URL the other LLM gave is wrong | `https://api.tezaurs.lv/v1/inflections/...` returns 404. `api.tezaurs.lv` is now the dictionary API and needs a key (contact api@tezaurs.lv). The free morphology service is `https://morpho-api.tezaurs.lv`, and it has a named-entity inflector. Verified, see 1.2. |
| GiellaLT has lang-lit | Technically true, practically useless | https://github.com/giellalt/lang-lit exists (LGPL-3.0, pushed 2026-11-06), but its lemma-count badge says 23 lemmas and maturity "Undefined". Compare lang-lav: 184K lemmas, Beta; lang-est-x-utee: 57K lemmas, Beta. There is no `giellalt/lang-est`. |
| "Morfuoklis" exists for Lithuanian | True | VDU morphological tagger built in the SEMANTIKA-2 project (CLARIN impact story: https://clarin.eu/impact-stories/accessible-and-result-driven-tools-lithuanian-language-processing). It is not published as a downloadable tool or API; the CLARIN-LT repository only has corpora annotated with it (e.g. SIMAS, handle 20.500.11821/105). Not usable from a Python service today. |
| EstNLTK + Vabamorf for Estonian | True | `pip install estnltk==1.7.5` (GPL-2.0-only OR Apache-2.0). Analysis, synthesis and a built-in speller all work. Verified, see 1.3. Limits on foreign names noted below. |

Other things the other LLM implied that turned out wrong or need correction:

- LanguageTool has no Lithuanian, Latvian or Estonian. The public API's `/v2/languages` (62 entries, fetched) lists none of them.
- COMET-Kiwi and xCOMET (the usual reference-free QE models) are CC-BY-NC-SA-4.0 and gated on HF. Not usable commercially. MetricX-24 (Apache-2.0) is the commercial-safe alternative.
- UDPipe 2 models served by LINDAT are CC BY-NC-SA. The Estonian UD treebanks (EDT, EWT) are also CC BY-NC-SA 4.0; the LT and LV treebanks are CC BY-SA 4.0.
- Wikidata lt/et labels are often empty for famous foreign players. Since 2024 Wikidata stores language-neutral names under the `mul` code and bots removed identical per-language labels. Even when present, the LT label is the original spelling ("Erling Haaland"), while Lithuanian media write "Erlingas Haalandas". See section 4.

## 1. Language tooling per language

### Summary table

| Need | Lithuanian (lt) | Latvian (lv) | Estonian (et) |
|---|---|---|---|
| Inflect a name into a case programmatically | No good open generator. Hunspell lt_LT can be unmunched for common nouns; foreign names need rules + LLM + curated glossary | Yes: `morpho-api.tezaurs.lv /inflect_phrase` (person/org/loc), free, no key | Partly: Vabamorf `synthesize()` works for known and simple names, fails or misanalyses some foreign names |
| Morph analysis (agreement checks) | UDPipe 2 (ALKSNIS) best in our test; Stanza `lt` weaker (small treebank, 56K tokens) | morpho-api `analyze_lvs`, `morphotagger`; Stanza/UDPipe on LVTB (330K tokens) | EstNLTK/Vabamorf (best); Stanza/UDPipe on EDT (non-commercial models) |
| Spell check | Hunspell lt_LT (ispell-lt, BSD-style; CLARIN-LT newer LGPL-3 version) via spylls | Hunspell lv_LV (LGPL-2.1) via spylls; also morpho-api OOV check; pyspellchecker has `lv` | Vabamorf speller (built into estnltk); hunspell et_EE (2004, LGPL) |
| LanguageTool | Not supported | Not supported | Not supported |
| Grammar checker with public API | None found | None found | None found (Vabamorf speller only) |

### 1.1 Lithuanian

What we tried:

- Hunspell lt_LT through `spylls` (pure Python, MIT) with the dictionary bundled in `phunspell` 0.1.6 (MIT wrapper; dictionary is ispell-lt, BSD-style). Loads in 0.2 s. Verified results: `krepšininkas` ok, `krepšinninkas` flagged with suggestion `krepšininkas`, `rungtynėse` ok, `įvartį` ok. It also accepted `įvarti` (missing ogonek), so diacritic errors that produce another valid word slip through. `Messi` flagged, so names need a user dictionary. Snippet: `snippets/hunspell_check.py`.
- A newer Lithuanian Hunspell dictionary (standard and standard+substandard, LGPL-3.0, 2025-02-07) is in the CLARIN-LT repository, handle 20.500.11821/64 (https://clarin-repo.lt). Its description says it supports analysis and synthesis; with real hunspell (`pip install hunspell` / pyhunspell, needs libhunspell) you could call `generate()`. Not tested.
- UDPipe 2 REST (https://lindat.mff.cuni.cz/services/udpipe/api/process, model `lithuanian-alksnis-ud-2.17-251125`). Verified on "Ar Žalgirio krepšininkai šiandien laimės rungtynes prieš Real Madrid komandą?": correct case/number on all nouns, `laimės` correctly a future-tense verb. It lemmatised `rungtynės` as `rungtynė` (plurale tantum error). Model licence is CC BY-NC-SA, so the hosted service is fine for a POC but not for production.
- Stanza 1.15.1 `lt` (ALKSNIS, Apache-2.0 code, CC BY-SA data). Verified, 43 s including model download. It tagged `laimės` as a genitive noun ("luck") instead of a verb. Treat its output as a weak signal.
- VDU tools (Kirčiuoklis accentuator at https://kalbu.vdu.lt/mokymosi-priemones/kirciuoklis/, Morfuoklis, Lemuoklis) are web forms with no documented API. semantika.lt did not respond on test day.

How Lithuanian media actually write foreign names (observed in search results, Nov 2026): 15min.lt "Kylianas Mbappe, Erlingas Haalandas, Lionelis Messi, Lamine'as Yamalis", "Kane'ui"; tv3.lt "K. Mbappe, L. Yamalis ir L. Messi"; LRT topic page `https://www.lrt.lt/tema/erlingas-haalandas`. Club names stay in the original spelling inside Lithuanian quotes: „Real Madrid“, „Manchester City“. So the rule set is: add Lithuanian endings to first names and to surnames that can take them (-as, -is, -ys, apostrophe + ending after a silent final letter: Lamine'as, Kane'ui), keep surnames ending in -i/-o/-e unchanged in most cases (Messi, Ronaldo, Mbappe), and never inflect a quoted club name; inflect the head noun before it instead ("„Real“ komandai"). LRT topic URLs (`lrt.lt/tema/<slug>`) are a cheap way to look up the canonical LT nominative for a person.

Recommendation for LT: build a per-entity glossary (nominative + the 6 case forms you need) offline, generated by an LLM from the LRT/15min nominative and checked by UDPipe re-analysis plus a human pass for the top ~500 entities. At runtime only look up forms.

### 1.2 Latvian

The public Tēzaurs morphology service is the best tool any of the three languages has.

Base: `https://morpho-api.tezaurs.lv` (no key; landing page reported version 2.202604.0). Endpoints listed on its index page include `/analyze_lvs/[word]`, `/inflect_general_lvs/[lemma]`, `/suitable_paradigm_lvs/[lemma]`, `/tokenize_lvs`, `/morphotagger/[query]`, `/inflect_people/[name]?gender=m|f`, `/inflect_phrase/[phrase]?category=person|org|loc`, `/normalize_phrase/[phrase]?category=...`; each has an `/en/` variant with English attribute names.

Verified requests and responses:

```
GET https://morpho-api.tezaurs.lv/inflect_phrase/en/Kristaps%20Porzi%C5%86%C4%A3is?category=person
{"Accusative":"Kristapu Porziņģi","Genitive":"Kristapa Porziņģa","Dative":"Kristapam Porziņģim","Nominative":"Kristaps Porziņģis","Gender":"Masculine","Locative":"Kristapā Porziņģī"}

GET .../inflect_phrase/en/Kristi%C4%81ns%20Ronaldu?category=person
{"Accusative":"Kristiānu Ronaldu","Genitive":"Kristiāna Ronaldu","Dative":"Kristiānam Ronaldu", ...}

GET .../inflect_phrase/en/%C4%92rlings%20H%C4%81lands?category=person
{"Accusative":"Ērlingu Hālandu","Genitive":"Ērlinga Hālanda","Dative":"Ērlingam Hālandam", ...}

GET .../inflect_phrase/en/R%C4%ABgas%20Futbola%20skola?category=org
{"Accusative":"Rīgas Futbola skolu","Genitive":"Rīgas Futbola skolas","Dative":"Rīgas Futbola skolai","Nominative":"Rīgas Futbola skola","Locative":"Rīgas Futbola skolā"}

GET .../analyze_lvs/en/futbolistam
[{"Number":"Singular","Guesswork":"None","Gender":"Masculine","Declension":"1","Wordform":"futbolistam","Part of speech":"Noun","Case":"Dative"}]

GET .../analyze_lvs/en/futbollists?guess=false   ->  []      (cheap out-of-lexicon check)
```

Known problem: quoted club names are mangled. `Mančestras "United"` came back as `Mančestru " United "`. Strip the quoted part, inflect the city part, and re-attach. Snippet: `snippets/latvian_morpho_api.py`. There is no published SLA or rate limit, so cache everything and do not call it on the hot path.

Latvian transliterates foreign names (Wikidata lv labels: "Lionels Mesi", "Krištianu Ronaldu", "Kilians Mbapē", "Ērlings Hālands", "Mohameds Salāhs", "Jons Valančūns"; Sportacentrs.com headline today: "Klēbo" for Klæbo). Wikidata lv labels are the best free starting point of the three languages.

Other LV resources:
- Hunspell lv_LV (Jānis Eisaks, LGPL-2.1, bundled in phunspell). Verified: `vartsargs` → suggests `vārtsargs`; `Porziņģis` unknown (needs user dictionary).
- `pyspellchecker` ships an `lv.json.gz` frequency list (MIT). It is a frequency-based checker, weaker than hunspell for an inflected language.
- GiellaLT lang-lav (GPL-2.0, 184K lemmas, Beta): FST analyser/generator. Needs HFST compilation; not tried.
- Stanza `lv` (LVTB) and UDPipe `latvian-lvtb-ud-2.17-251125` available.

### 1.3 Estonian

EstNLTK 1.7.5 (`pip install estnltk==1.7.5`, licence GPL-2.0-only OR Apache-2.0). I installed it in a Python 3.12 venv; a cp312 macOS arm64 wheel exists. Snippet: `snippets/estonian_vabamorf.py`.

Verified synthesis with `estnltk.vabamorf.morf.synthesize(lemma, form, partofspeech)`:

| Lemma | sg p | sg kom | sg g | Note |
|---|---|---|---|---|
| Flora | Florat | Floraga | Flora | correct |
| Žalgiris | Žalgirist | Žalgirisega | Žalgirise | correct |
| väravavaht | väravavahti | väravavahiga | väravavahi | correct |
| Messi (pos "") | Messit | Messiga | Messi | correct; with pos "H" returns [] |
| Ronaldo (pos "") | Ronaldot | Ronaldoga | Ronaldo | correct |
| Salah (pos "") | Salahit | Salahiga | Salahi | correct |
| Haaland (pos "") | haalanut | haalanuga | haalanu | wrong: guessed as verb "haalama" |
| Mbappé | [] | [] | [] | fails |
| Porziņģis | Porziņģisi | Porziņģisiga | Porziņģisi | questionable |
| "Meistrite Liiga" | [] | | | multi-word input not supported; inflect the head word |

Vabamorf's speller (`spellcheck()`) works without hunspell: `jalgpalllur` → suggests `jalgpallur`; `Messit` flagged (suggests Messi, Messist, ...), so names need a whitelist. Morph tagging of a whole sentence (`Text(...).tag_layer(["morph_analysis"])`) gave correct case on every token of "Kas Messi lööb täna Floraga mängus kaks väravat?".

Estonian keeps the original Latin spelling of foreign names (Wikidata et: "Erling Braut Håland", "Mohamed Salah"; ERR Sport headline today: "Kläbo"), and inflects them with case endings. So for ET, the glossary is mostly about the right case forms, plus apostrophe forms when pronunciation and spelling differ (Mbappé'ga style, check with a native editor).

Hunspell et_EE (2004, LGPL, 282K entries) also works through spylls but adds little over Vabamorf.

### 1.4 Dependency parsing / UD

| Language | UD treebank(s) | Tokens | Licence | Stanza | UDPipe 2 (LINDAT) |
|---|---|---|---|---|---|
| lt | ALKSNIS, HSE | 56,615 / 5,356 | CC BY-SA 4.0 | yes (`alksnis` default) | yes, CC BY-NC-SA model |
| lv | LVTB | 330,318 | CC BY-SA 4.0 | yes (`lvtb`) | yes |
| et | EDT, EWT | 437,787 / 90,583 | CC BY-NC-SA 4.0 | yes (`edt`) | yes |

Licences read from each treebank's README on GitHub (UniversalDependencies/UD_*). Stanza resources from `resources_1.10.0.json`. None of the three has a Stanza NER model. spaCy has no official lt/lv/et pipelines that I would rely on here (Lithuanian `lt_core_news_*` exist but are small; not tested).

For agreement checking in a buff (2-4 short options plus a question), you rarely need a parser. The common failures are a wrong case after a preposition or verb ("prieš + acc", "pret + acc/dat", Estonian comitative "-ga"), and options that do not share a case with each other. A morph analyser on each option is enough: check that all options in a set have the same case and number, and that the case matches the slot in the question template.

## 2. Machine translation and quality estimation

### 2.1 MT services

| Service | lt/lv/et | API | Observed / notes |
|---|---|---|---|
| DeepL API | all three | yes, key | Verified from DeepL's language table (https://developers.deepl.com/docs/getting-started/supported-languages): LT, LV, ET all have `glossaries:true, tagHandling:true, translationMemory:true, styleRules:true`, `textImprovement:false`. Glossaries matter: they are how you force "goal" → įvartis / vārti / värav. |
| Google Cloud Translation | all three | yes, key | Standard NMT; supports glossaries (Advanced edition). |
| TartuNLP (neurotolge.ee) | eng/est/lav/lit/ger/fin/rus/ukr + Finno-Ugric | Public, no key: `POST https://api.tartunlp.ai/translation/v2` | Verified. "Who will score the first goal for Real Madrid tonight?" → ET "Kes lööb täna õhtul Madridi Reali eest esimese värava?" (good); LT "Kas šįvakar pasieks pirmąjį "Real Madrid" tikslą?" and LV "Kurš šovakar būs pirmais Real Madrid mērķis?" (both translated "goal" as "objective"). "Which team will win the match?" was fine in all three. Docs: https://api.tartunlp.ai/translation/docs. No SLA; use for ET cross-checks and back-translation only. Snippet: `snippets/tartunlp_mt.py`. |
| Tilde MT | all three (Tilde's home market) | yes, commercial; credentials by request to mt@tilde.com (per the EU WEB-T page https://website-translation.language-tools.ec.europa.eu/automated-translation_en) | Not tested. Tilde also sells terminology (Tilde Term) and on-prem MT. Worth a sales call if Go3 wants an EU-hosted vendor. |

The TartuNLP result shows why the plan should be native generation with a glossary, not EN generation + MT. Sports senses of short words (goal, match, shot, assist, clean sheet) are where generic MT fails, and buffs are short enough that one wrong noun ruins the item.

### 2.2 Reference-free quality estimation

| Metric | Licence | lt/lv/et | Use |
|---|---|---|---|
| `Unbabel/wmt22-cometkiwi-da`, `Unbabel/wmt23-cometkiwi-da-xl/xxl` | CC-BY-NC-SA-4.0, gated | listed | Research only. Cannot ship. |
| `Unbabel/XCOMET-XL` / `XCOMET-XXL` | CC-BY-NC-SA-4.0, gated | listed | Research only. Gives error spans. |
| `Unbabel/wmt22-comet-da` | Apache-2.0 | listed | Needs a reference. Fine for offline eval against human-written gold buffs. `pip install unbabel-comet` (2.2.7). |
| `google/metricx-24-hybrid-{large,xl,xxl}-v2p6` | Apache-2.0, not gated | mT5 base covers all three | Has a QE (no reference) mode. Commercial-safe. Large is ~1.2B params; run on GPU offline or as a batch job. |
| GEMBA-MQM style LLM judge | depends on judge model | any | Prompt a strong model to list MQM errors (accuracy, fluency, terminology, style) with severity. This is what the pipeline's "LLM judge" stage should be. Calibrate it against 100-200 native-annotated buffs per language before trusting the scores. |

All licences above read from the Hugging Face model API on test day.

Note that QE metrics measure translation adequacy. For natively generated buffs there is no source sentence in the target language, so either QE the generated buff against the English fact sheet (works, since the facts are the source), or skip QE and rely on the validators plus the LLM judge.

## 3. Which LLMs are strongest in lt / lv / et

### 3.1 EuroEval (https://euroeval.com/leaderboards)

Data pulled from https://github.com/EuroEval/leaderboards (CSV files `<lang>_all.csv`; last commit 2026-04-20, so anything released after April 2026 is missing). Score is EuroEval's mean rank score (lower is better). Tasks: sentiment, NER, linguistic acceptability (ScaLA), reading comprehension, summarisation, knowledge, common-sense reasoning. Only the acceptability task directly tests grammar; nothing tests short creative generation.

| Model | LT pos (of 147 ranked) | LV pos (of 217) | ET pos (of 150) |
|---|---|---|---|
| gemini-3-pro-preview | #1 (1.32) | #2 (1.27) | #2 (1.30) |
| gemini-3-flash-preview (thinking) | #3 (1.48) | #12 (1.46) | #1 (1.29) |
| gpt-5 (2025-08-07) | no complete score | #1 (1.20) | no complete score |
| claude-sonnet-4-6 | #4 (1.52) | #10 (1.44) | #9 (1.68) |
| claude-sonnet-4-5 (thinking) | #6 (1.60) | #9 (1.40) | #7 (1.50) |
| gpt-5-mini | #8 (1.63) | #16 (1.53) | #13 (1.86) |
| gpt-4.1 | #10 (1.66) | #31 (1.78) | #10 (1.76) |
| gpt-5.2 | #13 (1.77) | #8 (1.40) | #15 (1.90) |
| gemma-4-31B-it (best open) | #14 (1.78) | #13 (1.47) | #12 (1.85) |
| gemma-3-27b-it | #15 (1.79) | #38 (1.81) | #17 (2.05) |
| Llama-3.3-70B-Instruct | #33 (2.00) | #41 (1.86) | #19 (2.09) |
| claude-haiku-4-5 | #38 (2.11) | #58 (2.06) | #48 (2.55) |
| EuroLLM-22B-Instruct-2512 | #51 (2.29) | #62 (2.16) | #23 (2.15) |
| EuroLLM-9B-Instruct | #54 (2.34) | #90 (2.53) | incomplete |
| TildeOpen-30b (base) | incomplete | #119 (2.85) | incomplete |

Claude Opus models are not on the EuroEval board. Script: `snippets/euroeval_ranks.py`.

### 3.2 Estonian: EKI leaderboard (moodupuu.eki.ee)

The Institute of the Estonian Language runs a native Estonian leaderboard; data at https://github.com/keeleinstituut/leaderboard-data-ui (results.json, last commit 2026-11-11, 101 models). Benchmarks: Keelenõu (240 language-norm questions from EKI's language advice service), idioms, terminology, trivia, trivia hard, book recommendations, propaganda resistance. Keelenõu and idioms are the closest public proxy for "writes correct, natural Estonian".

| Pos | Model | Overall | Keelenõu | Idioms | Terminology |
|---|---|---|---|---|---|
| 1 | anthropic/claude-fable-5.2 | 74.58 | 74.38 | 75.0 | 63.04 |
| 2 | openai/gpt-6-astra | 74.32 | 76.04 | 74.0 | 61.81 |
| 3 | openai/gpt-5.6-sol | 71.26 | 66.25 | 70.67 | 56.59 |
| 4 | google/gemini-4-argon | 69.81 | 77.5 | 70.0 | 57.54 |
| 5 | google/gemini-3.1-pro-preview | 69.52 | 61.88 | 72.33 | 57.03 |
| 13 | anthropic/claude-opus-5 | 64.1 | 65.42 | 58.33 | 55.94 |
| 14 | anthropic/claude-opus-5.5 | 63.68 | 68.75 | 62.0 | 56.45 |
| 30 | anthropic/claude-sonnet-5.5 | 52.08 | 62.5 | 47.33 | 38.99 |
| 52 | openai/gpt-4o | 41.14 | 47.29 | 45.67 | 32.61 |
| 88 | google/gemma-4-31b-it | 26.77 | 45.83 | 18.33 | 17.17 |
| 90 | google/gemma-3-27b-it | 25.84 | 36.67 | 19.33 | 17.75 |
| 96 | google/gemma-2-27b-it | 24.09 | 38.75 | 11.33 | 12.39 |

The gap between frontier closed models and the best open models is much larger here than on EuroEval: open models are roughly at a third of the frontier score on idioms. That matters for fan-facing copy, which is idiom-heavy. EuroLLM and TildeOpen are not on this board.

Also for Estonian: "Estonian Native Large Language Model Benchmark" (Lillepalu and Alumäe, arXiv 2510.21193, rev. Feb 2026) with a declension task; TartuNLP's HF collection "Estonian LLM Evaluation" (https://huggingface.co/collections/tartuNLP/estonian-llm-evaluation) has EstQA, grammar_et, winogrande_et, ifeval_et and more.

### 3.3 Lithuanian and Latvian benchmarks

- "Evaluating Large Language Models on Lithuanian Grammatical Cases", LoResLM 2026 (https://aclanthology.org/2026.loreslm-1.32.pdf). Small dataset, per-error-type accuracy; some case errors are near chance even for strong models (e.g. nominative wrongly used for direct address, where only Neurotechnology's LT models did moderately well). This is the most relevant published test for buff grammar.
- Neurotechnology LT-Llama-2 7B/13B (Informatica 2025, https://informatica.vu.lt/journal/INFORMATICA/article/1372/text): lowest human-rated error rate in the NoDaLiDa 2025 study (0.98%), but weak on knowledge and outdated as a base. Good evidence that monolingual tuning reduces grammar errors, not a model to deploy.
- LT history QA (arXiv 2501.09154, NB-REAL 2025): GPT-4o best across Baltic languages.
- "First Steps in Benchmarking Latvian in Large Language Models" (RESOURCEFUL 2025, https://aclanthology.org/2025.resourceful-1.22.pdf): Latvian Belebele, GPT-4o 94%, Llama 3.1 405B 92%, Gemma 2 27B / Qwen2.5 72B 91%.
- EuroEval's LT datasets (lrytas summarisation, lt_history, winogrande_lt, scala_lt) and LV datasets (scala_lv, mmlu_lv, copa_lv) are where most up-to-date numbers live.

I found no benchmark called "LT-Bench" or an Estonian "EstQA leaderboard" as such; EstQA is a dataset (TalTechNLP/EstQA).

### 3.4 Reading of the evidence

- Best quality: current frontier closed models (Gemini 3.x Pro, GPT-5.x/6, Claude Sonnet 4.5+/Opus/Fable). On EKI's Estonian norms test the top Anthropic and OpenAI models lead; on EuroEval (older snapshot) Gemini 3 Pro leads LT/ET and GPT-5 leads LV.
- Best open weights: Gemma 4 31B-it on EuroEval, clearly ahead of Gemma 3 27B, Llama 3.3 70B and EuroLLM-22B. On EKI's language-norm tasks every open model is far behind.
- None of these benchmarks measures what we produce (2-4 short, idiomatic, case-consistent options). We need our own eval set: ~150 buffs per language written or corrected by native sports editors, scored with the validators and an MQM-style human pass.

## 4. Sports reference data

### 4.1 Wikidata (verified)

Two scripts: `snippets/wikidata_wbgetentities.py` (Action API, preferred) and `snippets/wikidata_labels.py` (SPARQL). On test day WDQS answered HTTP 429 "Aggressively rate-limiting to 1 req / min ... during active wdqs outage", then recovered later. Use the Action API (`wbgetentities`, 50 ids per call) for anything automated.

SPARQL core (full version in the snippet):

```sparql
SELECT ?item ?en ?mul ?lt ?lv ?et ?wLt ?wLv ?wEt WHERE {
  VALUES ?item { wd:Q615 wd:Q11571 wd:Q380018 }
  OPTIONAL { ?item rdfs:label ?en  FILTER(LANG(?en)="en") }
  OPTIONAL { ?item rdfs:label ?mul FILTER(LANG(?mul)="mul") }
  OPTIONAL { ?item rdfs:label ?lt  FILTER(LANG(?lt)="lt") }
  OPTIONAL { ?item rdfs:label ?lv  FILTER(LANG(?lv)="lv") }
  OPTIONAL { ?item rdfs:label ?et  FILTER(LANG(?et)="et") }
  OPTIONAL { ?a schema:about ?item; schema:isPartOf <https://lt.wikipedia.org/>; schema:name ?wLt }
  OPTIONAL { ?b schema:about ?item; schema:isPartOf <https://lv.wikipedia.org/>; schema:name ?wLv }
  OPTIONAL { ?c schema:about ?item; schema:isPartOf <https://et.wikipedia.org/>; schema:name ?wEt }
}
```

Action API call: `https://www.wikidata.org/w/api.php?action=wbgetentities&ids=Q615|Q11571&props=labels|aliases|sitelinks&languages=en|mul|lt|lv|et&sitefilter=ltwiki|lvwiki|etwiki&format=json`

Results for 7 players, 8 clubs, 4 competitions (full output in `snippets/wikidata_output_2026-11-17.jsonl`; `[src]` = where the name came from):

| Entity | lt | lv | et |
|---|---|---|---|
| Lionel Messi | Lionel Messi [wiki title; no lt label] | Lionels Mesi [label] | Lionel Messi [wiki] |
| Cristiano Ronaldo | Cristiano Ronaldo [wiki] | Krištianu Ronaldu [label] | Cristiano Ronaldo [wiki] |
| Kylian Mbappé | Kylian Mbappé [wiki] | Kilians Mbapē [label] | Kylian Mbappé [wiki] |
| Erling Haaland | Erling Haaland [label] | Ērlings Hālands [label] | Erling Braut Håland [label] |
| Mohamed Salah | Mohamed Salah [label] | Mohameds Salāhs [label] | Mohamed Salah [label] |
| Kristaps Porziņģis | Kristaps Porziņģis [wiki] | Kristaps Porziņģis [wiki] | Kristaps Porziņģis [wiki] |
| Jonas Valančiūnas | Jonas Valančiūnas | Jons Valančūns | Jonas Valančiūnas |
| Manchester City | Manchester City FC | Manchester City F.C. | Manchester City FC |
| Real Madrid | Real Madrid CF | Madrides "Real" | Madridi Real |
| BC Žalgiris | Kauno Žalgiris | Kauņas "Žalgiris" | Kaunase Žalgiris |
| FC Flora | FC Flora Tallinn | FC Flora (alias Tallinas "Flora") | FC Flora |
| FC RFS | FK Rīgas Futbola skola | FC RFS | FC RFS [mul only] |
| Riga FC | Riga FC | Riga FC | Riga FC [mul only] |
| UEFA Champions League | UEFA Čempionų lyga | UEFA Čempionu līga | UEFA Meistrite Liiga |
| Premier League | Premier League [wiki] | Anglijas futbola Premjerlīga | Premier League [wiki] |
| EuroLeague | Eurolyga | Eirolīga | Euroliiga |
| Latvian Higher League | Virslyga | Latvijas futbola Virslīga | Virslīga |

Coverage observations:

- Every entity resolved to something in all three languages once you fall back label → Wikipedia title → `mul`. Raw lt/et labels were missing for 3 of 5 star footballers; that is the `mul` deduplication, not missing data.
- Competitions are well localised in all three. Clubs are mixed: LV and ET have native forms for big foreign clubs (Madrides "Real", Madridi Real) that the glossary should prefer; LT mostly keeps original names.
- Wikidata LT does not follow LT media convention for people. Media write "Erlingas Haalandas", "Kylianas Mbappe", "Lionelis Messi"; Wikidata/Wikipedia LT use the unadapted form. The LT glossary has to be built from media usage (LRT topic pages, 15min), not Wikidata.
- Aliases are sparse in lt, richer in lv (Valančiūnas has 5 lv aliases).
- Squad players of Baltic league clubs (Virslīga, Meistriliiga, LKL) were not tested individually; expect thin or missing labels for lower-profile players. Local league sites are the source for those.

### 4.2 Local league and federation sites (HTTP checked)

- Lithuania basketball LKL: https://www.lkl.lt/ (200).
- Latvia football federation: https://lff.lv (200). `virsliga.lv` did not resolve on test day.
- Estonia football (Meistriliiga, EJL): https://www.jalgpall.ee/ (200).

These have native-language player and club names, including Baltic players missing from Wikidata. No public APIs found; scrape squad pages once per season with permission.

### 4.3 Commercial sports data with localisation

- Sportradar / Betradar Unified Odds: the integration guide's language table lists `et`, `lv`, `lt` (and states that for languages without specific translations they return English names). Source: https://iodocs.betradar.com/unifiedsdk/Betradar_Unified-Odds_Developer_Integration.pdf. Endpoints take the language in the path (e.g. `docs.sportradar.com/uof/...` fixture endpoint has a `language` path parameter). The Sportradar Sports Data API (e.g. NFL v7) enumerates a smaller language set that did not include Baltic languages in the snippet I saw. Ask Sportradar which products return lt/lv/et competitor and player names, and how much is real translation versus English fallback.
- Smaller vendors that list lt/lv/et as data languages: live-score-api.com (lt listed), worldcupapi.com (et, lt listed), sportapi.net (lv, lt listed). Unverified quality.
- API-Football: no localisation parameter that I know of; not checked in detail.

Go3 / All Media Baltics already publish native-language sports copy, so the best glossary source may be their own CMS. Ask for it.

### 4.4 Native sports text (few-shot, RAG, glossary mining)

Verified RSS feeds (HTTP 200 with items on 2026-11-17; `snippets/sports_rss.py`):

| Lang | Feed | Note |
|---|---|---|
| lt | https://www.lrt.lt/tema/sportas?rss | 100 items, CDATA titles (also works: `https://www.lrt.lt/naujienos/sportas?rss`) |
| lv | https://www.lsm.lv/rss/ | All sections; filter links containing `/raksts/sports/` |
| lv | https://sportacentrs.com/rss | Sports only, 35 items |
| et | https://sport.err.ee/rss | Sports only, 50 items |
| et | https://www.err.ee/rss | General news |

Returned HTTP 403 to a scripted client: 15min.lt/rss/sportas, lrytas.lt/rss/sportas, basketnews.lt/rss/, delfi.lv/rss/?channel=sports, sport.delfi.ee/rss. `delfi.lt/rss/feeds/sport.xml` answered 200 but the channel was a generic "Global LT latest articles" feed.

Use these for headline-style few-shots and to mine how outlets inflect names. Store headline, link and date; do not store or redistribute full articles without a licence.

Corpora:
- Estonian National Corpus (Eesti keele ühendkorpus, latest 2023): searchable at https://korp.keeleressursid.ee (200) and via Sketch Engine (https://www.sketchengine.eu/estonian-national-corpus/). `korpused.keeleressursid.ee` returned 503 on test day. Bulk downloads go through the Estonian CLARIN centre (https://metashare.ut.ee, 200).
- Latvian LVK2022 balanced corpus: https://www.korpuss.lv/id/LVK2022 (200). Latvian CLARIN repository: https://repository.clarin.lv (200).
- Lithuanian: CCLL (Dabartinės lietuvių kalbos tekstynas) at https://tekstynas.vdu.lt timed out on test day; CLARIN-LT (https://clarin-repo.lt, https://clarin.vdu.lt) has SIMAS (10M words, morphologically and syntactically annotated, "NewGenLTU openRAIL-D" licence, 2026-05-14) and LITUND (CC BY-NC-SA).
- EuroEval's `lrytas` (LT news summaries) and TalTechNLP `ERRnews` (ET) on HF are small, clean news sets usable as style references.

Corpora are useful for building term lists and frequency checks. For few-shot prompting, 20-40 hand-picked native buffs per language will do more than any corpus.

## 5. Recommended POC stack

### 5.1 Precompute (offline, per season / nightly)

1. Entity table: for each player, club, competition in scope, store QID, en name, and per-language nominative. Source order: Go3 CMS (if available) → LT media form (LRT topic pages) / LV Wikidata label / ET Wikidata label or original spelling → `mul` → en. Pull with `wbgetentities` in batches of 50.
2. Case forms per entity and language:
   - lv: `morpho-api.tezaurs.lv/inflect_phrase` (person/org/loc), cached.
   - et: Vabamorf `synthesize()` with `partofspeech=""`, then reject any form that re-analyses to a different lemma; LLM fills the gaps (Haaland, Mbappé).
   - lt: LLM generates the forms from the media nominative using the rules in 1.1; UDPipe or Stanza re-analysis checks case labels.
   - A native editor reviews the top N entities per language once. This is the step that removes most visible errors, and it is cheap (a few hundred rows).
3. Sports glossary (~150 terms per language: goal, own goal, penalty, corner, yellow card, rebound, three-pointer, overtime, clean sheet...), each with case forms. Load the same glossary into DeepL if DeepL is used anywhere.
4. Few-shot bank: 20-40 native buffs per language per buff type, written or corrected by native editors, plus headline examples from the RSS feeds.
5. Spell-check user dictionaries: add all entity forms to the hunspell/Vabamorf whitelists so names stop showing up as errors.

### 5.2 Runtime (per buff)

1. Facts in (English, structured).
2. Entity linker swaps entity IDs for the target-language forms. Prefer templates where the generator asks for a slot ("{player:dat}") and code fills the inflected form from the table. This removes the largest error class.
3. Generate natively with a frontier model: system prompt in the target language, glossary, 5-8 few-shots, JSON output (question + options). Based on section 3, start with a current Claude (Sonnet 4.5+/Opus) or Gemini 3.x Pro/Flash model and A/B them on our own eval set; Gemma 4 31B-it is the open-weight fallback if self-hosting is required.
4. Validators (local, all under ~50 ms each after warm-up):
   - length limits, option count, no duplicates, numbers match the facts;
   - entity forms appear only as forms present in the table;
   - spell check (spylls + whitelist for lt/lv; Vabamorf for et);
   - case agreement across options (Vabamorf for et; Tēzaurs analysis results cached or the LVTB Stanza model for lv; Stanza/UDPipe for lt, treated as a soft signal).
5. LLM judge (GEMBA-MQM style, different model family from the generator if possible), only for buffs that pass validators. Output: error list + severity.
6. Repair loop: send validator/judge errors back to the generator once or twice; if still failing, fall back to a pre-approved template buff.

### 5.3 Cost and latency notes

- Model calls dominate. A buff is ~150-300 output tokens and ~2-4K input tokens with glossary and few-shots; use prompt caching for the static part (system prompt, glossary, few-shots). Generator + judge + at most one repair is 2-3 calls, roughly 2-8 s end to end with a fast model; buffs are not latency critical to the second, but pre-generate for scheduled moments (kick-off, half-time) where possible.
- Local validators: spylls loads a dictionary in 0.2-0.9 s (load once at startup); Vabamorf and Stanza need a long-lived worker process (Stanza first load ~40 s with download). Keep them in a sidecar service, not inside request handlers.
- External free services (morpho-api.tezaurs.lv, TartuNLP, UDPipe LINDAT, Wikidata) have no SLA and some have non-commercial terms. Use them only offline/precompute and cache results.
- Paid MT (DeepL, Google) is only needed if we add an MT-based cross-check; at buff lengths (~200 characters) cost is negligible. Check current list prices before quoting them.
- Licences to keep out of production: COMET-Kiwi/xCOMET (NC), UDPipe LINDAT models (NC), UD Estonian treebank-derived models (NC data), LanguageTool wrapper (GPL-3, and useless here anyway). EstNLTK is dual GPL-2.0/Apache-2.0, so use it under Apache-2.0.

### 5.4 Things not verified in this pass

- Lithuanian Hunspell (CLARIN-LT version) generation via pyhunspell.
- GiellaLT lang-lav / lang-est-x-utee FSTs (need HFST build).
- MetricX-24 QE on Baltic buffs (model not downloaded).
- Tilde MT and Sportradar Baltic name coverage (need accounts).
- Rate limits of morpho-api.tezaurs.lv and api.tartunlp.ai.
