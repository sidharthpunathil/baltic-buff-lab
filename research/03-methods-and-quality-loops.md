# 03. Methods and quality loops for Baltic-language buffs

Scope: how teams that ship good multilingual content at scale get grammatical, natural output, and which of their mechanisms JoinInLive should copy for Lithuanian (lt), Latvian (lv) and Estonian (et) buffs. Research date: 2026-11-17.

The buff problem in one paragraph: a buff is a question of about 60 to 120 characters, two to four options of one to four words each, and a short reveal line. It is generated live from match events, under latency pressure, and shown on a phone. Today the pipeline writes English and translates it literally. Natives reject the output. That matches the research: literal translation is the documented source of "translationese", and short, idiomatic, culturally loaded text (sports banter, puns, idioms) is where LLM translation fails most.

## 1. What the evidence says, in short

1. Translating is the wrong task framing. A 2025 ACL study found LLMs produce unnatural, literal output inside a "translate" prompt even though they can write naturally in the target language; the bias comes from supervised translation data. Prompting for "naturalness" did not reliably help and sometimes made GPT-4 worse. Asking the model to polish its own output cut translationese from 43% to 25%. Sources: https://aclanthology.org/2025.acl-long.630.pdf, https://slator.com/translationese-remains-challenge-for-large-language-models-study-finds
2. Model choice matters more for Estonian than people expect. WMT25 human evaluation (ESA protocol), English to Estonian: human reference 83.1, Gemini 2.5 Pro 78.8, GPT-4.1 72.2, ONLINE-B 60.2, Claude-4 53.0, EuroLLM-22B 47.2, Gemma-3-27B 45.9. That is a 26-point spread between frontier models on one language. Source: https://steinst.is/files/2025_wmt_sharedtask.pdf and https://machinetranslate.org/wmt25 (Gemini 2.5 Pro won en-et unconstrained). WMT25 did not run en-lt or en-lv, so we have no equivalent table for those two and must benchmark ourselves.
3. Open-weight models are weaker in lt/lv/et than in Czech of similar size, and the gap is largest when generating in those languages. Source: https://arxiv.org/html/2501.03952v1. TildeOpen-30B (Latvian company Tilde, CC-BY-4.0, Oct 2025) was built for these languages and tokenizes 41% / 37% / 28% more efficiently than Llama-3 in lv / lt / et. Sources: https://slator.com/tilde-unveils-european-multilingual-ai-model-with-safeguards-against-disinformation, https://arxiv.org/html/2603.08182v2
4. Glossaries in the prompt work. The WMT25 terminology task was won at sentence level by o3 with terminology injected into the prompt, and the document-level winner also used glossary prompting. Source: https://aclanthology.org/2026.wmt-main.112.pdf. WMT26 systems cap the injected block at about 200 locally relevant term pairs and tell the model to adapt term morphology and agreement. Source: https://www2.statmt.org/wmt26/pdf/2026.wmt-1.51.pdf. Hard lexical constraints, by contrast, produce malformed output in morphologically rich languages: https://www.emergentmind.com/topics/terminology-constrained-machine-translation
5. LLM judges are good enough to rank systems, with caveats at segment level. GEMBA-MQM (GPT-4, three-shot, language-agnostic prompt) reached 96.5% system-level pairwise accuracy on WMT23 without references; the authors warn against using it as the only evidence. Sources: https://arxiv.org/abs/2310.13988, https://voicefrom.ai/blog/gemba-mqm-v2-translation-quality. WMT25 itself used GEMBA-ESA with two independent LLM judges for its automatic ranking.
6. Round-trip translation is a poor quality signal. BLEU between source and round-trip output was historically a poor predictor; even embedding-based round-trip QE lost correlation among the top systems. Source: https://aclanthology.org/2020.eamt-1.11.pdf
7. Post-edits are preference data. "Post-edits Are Preferences Too" (WMT24) trained on (machine output, human post-edit) pairs with preference optimization and raised the model's preference for post-edits to 68% on test data. A 2025 follow-up used the same idea to teach terminology. Sources: http://www2.statmt.org/wmt24/pdf/2024.wmt-1.122.pdf, https://aclanthology.org/2025.emnlp-industry.42.pdf

## 2. How the reference companies do it

### Duolingo

- Generation by "Mad Lib" prompt: fixed rules per exercise type (number of options, max 75 characters), variable slots filled automatically (language, CEFR level, theme) or by the learning designer (grammar focus). The model returns ten candidates; the designer picks three and edits them for naturalness. Duolingo states plainly that the raw outputs "follow the rules, but some of them sound a little stilted or unnatural", and that the language experts "always have the final say". Source: https://blog.duolingo.com/large-language-model-duolingo-lessons
- Over-generate, filter by model, then human review. Commentary on the pipeline describes candidates passing algorithmic gates (Birdbrain difficulty scores and quality metrics) before a human sees them. Source: https://drphilippahardman.substack.com/p/duolingos-ai-revolution. Birdbrain itself: https://blog.duolingo.com/learning-how-to-help-you-learn-introducing-birdbrain/
- Accepted-answer sets. Each English prompt in a Duolingo course has many accepted translations weighted by how often learners produce them. The STAPLE dataset has means of 56 to 342 accepted translations per prompt depending on language. Sources: https://sharedtask.duolingo.com, http://sharedtask.duolingo.com/papers/khayrallah.staple20.pdf, https://blog.duolingo.com/using-ai-to-open-up-bottlenecks-in-course-content-creation
- User error reports feed back into the model. In Duolingo Max, learners long-press a message to report it with a reason, and the team uses reports to improve the model. Humans write the role-play scenarios and opening lines; the model only continues. Source: https://blog.duolingo.com/duolingo-max

### Babbel

- No translated curriculum. Each language pair is written separately by a didactics team of 150+ linguists, teachers and editors, and the course differs depending on the learner's native language. Sources: https://www.babbel.com/babbel-language-experts, https://www.smarterlanguage.com/the-smarter-language-review-of-babbel. This is the strongest data point for "native-first" over "translate".

### Sportradar (betting data)

- Market and outcome names are templates with typed placeholders: `{$competitor1}`, `{$competitor2}`, `{$event}`, plus specifiers like the handicap line. Market names are translated into every supported language; entity names (teams, players, tournaments) come from a separate translated entity store and fall back to English. Operators can override any translation with their own. Sources: https://iodocs.betradar.com/unifiedsdk/Betradar_Unified-Odds_Developer_Integration.pdf, https://docs.sportradar.com/uof/introduction/key-concepts/outrights
- Lesson for us: the high-volume, must-never-be-wrong parts of sports copy (market names, outcomes like "1X2", "Draw no bet") are pre-localized templates, not generated text.

### Data-to-text sports summaries

- Prosebot (zerozero.pt, Portuguese football) runs template-based NLG to draft match summaries for hundreds of thousands of users; a community of readers post-edits before publication. Its stated weakness is low diversity. Source: https://aclanthology.org/2024.lrec-main.15.pdf
- Neural data-to-text on RotoWire and MLB is known for hallucinating facts not in the box score; planning-based neural models help but do not remove the problem. Source: https://ratishsp.github.io/assets/pdf/inf_phd_thesis.pdf. The field's practical split: templates for facts, models for variety.

### Locale style guides

Microsoft publishes localization style guides for all three languages: index https://learn.microsoft.com/en-us/globalization/reference/microsoft-style-guides; Lithuanian https://web.archive.org/web/20190124205442/http://download.microsoft.com/download/d/9/b/d9b3b746-78ec-4049-bc43-c0f744199f71/lit-ltu-StyleGuide.pdf; Latvian https://download.microsoft.com/download/c/9/c/c9c901d9-8d73-4a07-bda2-e9177cc0e965/lav-lva-StyleGuide.pdf; Estonian https://download.microsoft.com/download/7/7/3/7734c896-d576-44f6-bf00-66350cb24be9/est-est-StyleGuide.pdf.

Rules pulled from the Lithuanian guide (read in full) that apply directly to buffs:

- Address the user with 2nd person plural (jūs), lower case when written; usually omit the pronoun entirely.
- Avoid word-to-word translation; split or restructure sentences so the text reads as if written in Lithuanian.
- Lithuanian uses possessive pronouns far less than English; drop them when they carry no meaning ("Your prediction" should not become "Jūsų prognozė" by reflex).
- Placeholders: anticipate what fills the slot so the sentence stays grammatical. A slot filled with a nominative form ("Jūsų {doctype} parengtas") is marked wrong; the fix is to add a governing noun or set the slot off with brackets, a colon or a dash. This is exactly the team-name-in-a-sentence problem buffs have.
- Gender: options must agree with the noun in the question (the guide's example: colours are feminine because "spalva" is feminine). Prefer forms that work for both genders when possible.
- Quotation marks are „x“; tooltips have no final period; error messages end with a period.
- Sentence fragments are encouraged for a conversational tone.

The Proton Lithuanian community guide adds: en dash without spaces in number ranges (700–800 EUR), spaced en dash between clauses, no apostrophes, "&" becomes "ir". Source: https://localize.proton.me/t/guidance-for-lithuanian/559

Latvian and Estonian guides: I could not extract readable text from the two PDFs with the tools available, so their specific rules are not quoted here. A native reviewer should pull the address form, quotation marks, number and date format, and placeholder sections from each into our per-locale style sheet. For Latvian, practitioner guidance says to pick Jūs or tu once and document it, and to watch case agreement when addressing the reader (https://translatedesk.io/blog/latvian-help-center-translation-complete-guide). For a fan game, informal address is plausible in all three languages, but that is a product decision for native reviewers, not something to infer from Microsoft's software-UI defaults.

### Morphology tooling

- Latvian: a full computational morphology (analysis and synthesis, inflection tables for Tēzaurs.lv, available as an API) from the University of Latvia. It has been used specifically to inflect named entities and generate word lists for games. Source: https://aclanthology.org/2024.lrec-main.20.pdf
- Estonian: the Institute of the Estonian Language's analyzer (the lineage behind Vabamorf / EstNLTK) handles an average of 33 forms per word, including words not in the dictionary. Source: https://arhiiv.eki.ee/teemad/morfoloogia/viks1.html
- Lithuanian: not verified in this pass; check Semantika.lt and VDU tools before choosing.

## 3. Mechanisms: why, how for buffs, cost, priority

Each entry: mechanism, why it works, how to apply to buffs, cost/complexity, priority.

### M1. Native-first generation (transcreation), not translation. P0

- Why: the translationese finding (section 1, item 1) and Babbel's model. A model asked to write a Lithuanian quiz question about a corner kick draws on Lithuanian sports text; a model asked to translate an English question copies English structure, possessives, word order and idioms.
- How: feed the same structured event payload (match state, event type, players, teams, minute, score) to a per-locale generation prompt written in or about that locale. The English buff is not an input. If the English and Baltic buffs must ask the same question (for cross-locale analytics or shared answer keys), pass a language-neutral spec instead of English text: `{buff_type: prediction, subject: next_goal, options: [team_home, team_away, no_goal], window: 10min}`. Each locale renders the spec natively. The answer key lives in the spec, so it cannot drift across languages.
- Cost: low. One prompt per locale plus a spec schema. Latency is the same as today.

### M2. Locale style sheet and sports glossary injected into every prompt. P0

- Why: glossary prompting won WMT25 terminology tasks; LLMs adapt morphology when told to. Style guides encode what a native editor would otherwise fix by hand.
- How: one file per locale, under 1-2k tokens: address form, punctuation (quotes, dashes, ranges), number/time format ("65'" vs "65 min."), forbidden calques, and a football glossary (offside, corner, penalty, yellow card, extra time, clean sheet, hat-trick, VAR, "1X2"). Each glossary entry stores the lemma plus the forms we actually need (nominative, genitive, and the case after common question verbs) and a note like "adapt case to the sentence". Retrieve only the entries relevant to the current event to keep the prompt short. Seed from native reviewers and from how local broadcasters and bookmakers already phrase markets; let natives own the file.
- Cost: low engineering, a few hours of native time per locale to seed, then ongoing edits.

### M3. Typed slots and morphological generation for entity names. P0

- Why: team and player names are where morphology breaks first. The Lithuanian Microsoft guide flags nominative placeholders dropped into sentences as an error. Sportradar keeps entity names in a separate translated store for the same reason.
- How: maintain a per-locale entity table: each team and player with the localized name and its case forms (nom, gen, dat, acc, loc at minimum; Estonian needs more: partitive, illative, inessive, elative, adessive, etc.). Populate it once per squad with a morphology tool (Latvian synthesizer; Estonian Vabamorf) or a careful LLM pass checked by a native, and cache it. Two ways to use it: (a) give the LLM the full form table in the prompt and require it to use only those forms, then validate; or (b) for fixed-format buffs, render templates with `{team_home:gen}`-style typed slots, as Sportradar does with `{$competitor1}`. Foreign surnames are a known trap in Lithuanian and Latvian, which add native endings to foreign names (e.g. Latvian -s, Lithuanian -as/-is); the table is where that decision is made once and reviewed.
- Cost: medium. A small service plus a review pass per club. Pays off on every buff.

### M4. Pre-localized templates for the high-frequency buff shapes; free generation for the rest. P0 for templates, P1 for the hybrid

- Why: templates are grammatical by construction (Prosebot, Sportradar). Their weakness is monotony, which matters for engagement.
- How: native writers produce 5-10 variants per common buff shape (next goal, who wins the half, will there be a card before 70', rate the goal, man of the match) per locale, with typed slots. The LLM's job for these becomes picking and filling a variant and writing the reveal line. Novel moments (a weird VAR call, a record) go to free native generation (M1) with the full validation stack. Track which path each buff took so you can compare quality and engagement.
- Cost: medium native writing time up front (roughly 50-100 template variants per locale), low engineering.

### M5. Over-generate, auto-filter, then pick (Duolingo pattern). P0

- Why: Duolingo generates ten and keeps three. Quality-aware reranking (generate N, score with a QE model or judge, keep the best) is linear in N and is the standard way to buy quality with compute. Sources: https://arxiv.org/html/2310.06707v4, https://aclanthology.org/2025.iwslt-1.3.pdf
- How: request 3-5 candidates per buff in one call (structured output). Run cheap deterministic checks first (M6), then score survivors with the LLM judge (M8) or a QE model, and show the operator the top one with the runner-up one click away. For auto-published buffs, publish only if the top score clears a threshold; otherwise fall back to a template (M4) or hold for the operator.
- Cost: low to medium. More tokens per buff; candidates can be generated in parallel so latency grows little.

### M6. Deterministic validators before any human or judge sees the text. P0

- Why: cheap, exact, and they catch the embarrassing failures (wrong diacritics, English leakage, overflow) that erode trust fastest.
- How, per locale: length limits per UI field measured in rendered characters; required diacritics alphabet (lt ą č ę ė į š ų ū ž; lv ā č ē ģ ī ķ ļ ņ š ū ž; et õ ä ö ü š ž) and a check for ASCII-stripped words via a spellchecker (Hunspell dictionaries exist for all three); English-token leakage; options unique and mutually exclusive; exactly one correct option for quizzes; correct option text matches the spec; entity forms match the table from M3; banned-phrase list from the style sheet; punctuation rules (quotes „ “, no trailing period on options). A morphological analyzer can also flag words it cannot parse, which catches invented forms.
- Cost: low. A few hundred lines of code plus dictionaries.

### M7. Self-refine step: draft, critique against the style sheet, rewrite. P1

- Why: the translationese study found self-polish cut literal phrasing from 43% to 25%; Andrew Ng's translation-agent does translate, reflect, improve and reports results that are sometimes better and sometimes worse than commercial MT (https://github.com/andrewyng/translation-agent). Generic "be natural" instructions did not help; a critique against concrete rules is the useful version.
- How: one extra call that gets the candidate plus the style sheet and returns a list of specific problems (case, agreement, calque, register, length) and a revised version. Run it only when validators or the judge flag something, to keep latency down. Do not loop more than once; repeated self-editing can drift meaning.
- Cost: low engineering, one extra call on a subset of buffs.

### M8. LLM-as-judge with an MQM-style error list, calibrated against natives. P0 for offline eval, P1 online

- Why: GEMBA-MQM and GEMBA-ESA are the current standard for reference-free ranking; WMT25 used two independent LLM judges. Error spans with categories are actionable; a bare score is not.
- How: judge prompt in section 5. Use a different model family from the generator, or two judges, to avoid self-preference. Before trusting it, measure agreement with native raters on the golden set (section 4). Use it offline to compare prompts and models, and online as the reranker in M5.
- Cost: low to medium per call. The real cost is calibration time with natives.

### M9. Pick the generator per locale by measurement. P0

- Why: WMT25 en-et spread of 26 ESA points between frontier models. No public equivalent exists for lt/lv.
- How: run the golden set (section 4) through 3-4 candidate models (current Gemini Pro, GPT, Claude, and TildeOpen-30B as the open option), using the native-first prompt. Route each locale to the winner. Re-run quarterly; rankings move with every release.
- Cost: low. One afternoon of runs plus native rating time.

### M10. Reference-free QE model as a cheap second signal. P2

- Why: CometKiwi gives a 0-1 score from source and output with no reference (https://github.com/Unbabel/COMET). Unbabel used it to curate fine-tuning data for TowerLLM (https://finance.yahoo.com/news/unbabel-says-ai-model-dethroned-110000059.html).
- Caveat for us: QE models score translation of a source. Under native-first generation there is no source sentence, only a spec, so CometKiwi only applies to the translate path or to an English rendering of the same spec. It is also trained on longer sentences than buff options. Treat it as an extra feature, not a gate.
- Cost: medium (GPU hosting or an API, license acknowledgement on Hugging Face).

### M11. Operator edit capture as the data flywheel. P0 to capture, P1 to use

- Why: post-edits are preference pairs (WMT24 paper above). Edit distance over time is the cheapest quality KPI there is, and Duolingo-style user reports cover what operators miss.
- How:
  - Store every generated candidate, the one shown, and the final published text per buff and locale, plus who edited, time spent editing, and the event context. This is a write path, so follow the repo's write-behind rules and test that rows land in Postgres.
  - Compute HTER-style character and word edit rate between shown and published. Track it per locale, buff type, model, prompt version and path (template vs free). Edit time matters too; edit distance alone misses effort (https://slator.com/a-quick-primer-on-edit-distance-a-key-metric-in-post-editing-machine-translation).
  - Ask editors for one tap of reason on each edit, using the error categories from section 4 (grammar, unnatural, term, fact, tone, too long). This turns edits into a labeled error taxonomy for free.
  - Add a long-press "report wording" on the viewer side, as Duolingo Max does.
  - Use the data in this order: (1) mine edits for new glossary entries and banned phrases (weekly, by a person); (2) add good edited buffs to a retrieval pool of few-shot examples per locale and buff type, so the prompt shows real approved native buffs (M12); (3) promote stable, typical buffs into the golden set; (4) only after a few thousand pairs per locale, consider preference tuning (M13).
- Cost: low to capture, medium to use well.

### M12. Retrieval few-shot from approved native buffs. P1

- Why: in-context examples move style and terminology more reliably than instructions, and Duolingo notes the model "can learn a lot from seeing the examples of Duolingo content". Examples written by natives carry the register we want.
- How: index approved buffs by locale, buff type, event type and sport. At generation time retrieve 3-5 nearest examples and put them in the prompt. Seed with native-written templates (M4) before operator data exists.
- Cost: low to medium (embedding index; can live in Postgres with pgvector or in Redis).

### M13. Fine-tuning or LoRA. P2

- When it helps: when you have thousands of approved in-domain pairs per locale and an open model you can host (TildeOpen-30B is the obvious base for lt/lv/et), or when prompt length and latency become the bottleneck. WMT24 notes most submitted systems fine-tuned a pretrained LLM; preference tuning on post-edits beat SFT alone in the WMT24 post-edit paper.
- When it does not: before the golden set, glossary, templates and edit capture exist. Prompting a frontier model with M1 to M8 is cheaper to iterate and probably closes most of the gap.
- Cost: high (data curation, hosting, eval, maintenance per locale).

### M14. Round-trip translation as a check. Do not use as a gate

- Why not: poor correlation with quality (Moon et al. 2020). Back-translation mostly tests whether meaning survived, and a fluent but unnatural Lithuanian sentence round-trips perfectly; it is blind to exactly the problem natives are complaining about.
- Acceptable use: a cheap faithfulness alarm when the buff came through a translate path, to catch a flipped negation or wrong team. The spec-based answer key (M1) is a better guard for that.

### M15. Self-consistency and ensembles. P2

- Generating multiple candidates and picking by agreement or by judge is already covered by M5. Using two judges and taking the minimum score is a cheap way to reduce judge noise for publish decisions. Beyond that, ensembles add cost without a clear payoff for 100-character texts.

### M16. A/B on engagement, after quality is fixed. P1

- Why: grammar is a floor, not the goal. Duolingo optimizes learning and engagement on top of correctness.
- How: once a locale's judge-and-human scores are stable, A/B prompt or template variants on answer rate, time to answer and drop-off per buff. Never A/B a variant that has not passed the quality gate.

## 4. Evaluation protocol

### Golden set

- Size: 150 buffs per locale to start (450 total), growing to 300 per locale from operator edits. 150 is enough to separate systems that differ by about 0.3 points on a 5-point scale with two raters, and small enough for one native to rate in a working day.
- Composition per locale: 45 polls, 40 quizzes, 40 predictions, 25 star ratings. Spread across event types (goal, card, substitution, VAR, half-time, full-time, pre-match, stoppage time) and include hard cases on purpose: foreign player names that need declension, numbers and minutes, negation ("Will there be no goal…"), comparatives, team names that are plural or feminine, options that must agree in gender and case with the question.
- Each item stores: the language-neutral spec, the event context, the correct answer, and one or two native reference buffs written from scratch by a native (not translated). References enable reference-based scoring later but the rubric does not require them.
- Keep 30 items per locale as a hidden test split nobody uses for prompt tuning.

### Raters

- Two native raters per locale, ideally football fans; one should have editing or localization experience. Freelance rates make this a few hundred euros per locale per full pass.
- Rater calibration: both rate the same 20 items, discuss disagreements, then rate the rest. Report agreement (quadratic-weighted Cohen's kappa per dimension; aim for 0.6 or higher). Include 5 control items with known planted errors to catch inattentive raters, as WMT's ESA protocol does with control tasks.
- Raters also mark error spans with a category and severity (minor, major, critical), ESA style: faster than full MQM and close in quality (Kocmi et al. 2024, referenced at https://www.alphaxiv.org/@tom-kocmi).

### Rubric (each dimension scored 1-5, applied to the whole buff: question, options, reveal)

Grammar and orthography
- 5: No errors. Case, agreement, diacritics and punctuation all correct.
- 4: One minor slip a native would barely notice (e.g. comma placement).
- 3: One clear error (wrong case on a name, missing diacritic) that does not block understanding.
- 2: Several errors, or one that makes a phrase hard to parse.
- 1: Ungrammatical throughout or wrong language mixed in.

Naturalness and idiomaticity
- 5: Reads like a local sports editor wrote it; you could not tell it was machine-made.
- 4: Natural, with one slightly bookish or stiff choice.
- 3: Understandable but clearly translated: English word order, needless possessives, calques.
- 2: Awkward enough that a fan would laugh at it or screenshot it.
- 1: Word-for-word English in Baltic words.

Terminology
- 5: Every football term is what local broadcasters and fans use.
- 4: One term is correct but not the most common choice.
- 3: One wrong or English term where a local one exists.
- 2: Several wrong terms, or a wrong term that changes meaning (e.g. "free kick" vs "penalty").
- 1: Terminology makes the buff confusing.

Factual faithfulness (to the spec and match data)
- 5: Question, options and answer exactly match the spec and the match state.
- 4: Faithful, with a harmless omission (e.g. minute not mentioned).
- 3: A detail is wrong but the answer key is still correct.
- 2: The question can be read two ways, or an option overlaps another.
- 1: Wrong answer key, wrong team or player, or a negation flipped.
  Any 1 here is a release blocker regardless of other scores.

Tone and engagement
- 5: Fits a live fan moment; energetic, would make you want to tap.
- 4: Fine and friendly, a bit flat.
- 3: Neutral, reads like a form.
- 2: Wrong register (too formal, bureaucratic, or inconsistent address form).
- 1: Off-putting, condescending, or insensitive.

Length and UI fit
- 5: Fits all fields on a 320px screen with room to spare; options are short and parallel.
- 4: Fits; one option is noticeably longer than the others.
- 3: Fits only on larger screens, or options are not parallel in structure.
- 2: Truncates or wraps badly on common phones.
- 1: Breaks the layout.

Pass bar for a locale to ship auto-published buffs: mean of 4.0 or higher on grammar, naturalness and terminology; 4.5 or higher on faithfulness; zero faithfulness scores of 1 across the golden set; and at least 85% of buffs rated 4+ on naturalness by both raters.

### Automatic metrics tracked alongside

- Validator pass rate (M6).
- LLM judge scores per dimension, with Spearman correlation against the human mean per dimension. Trust the judge for a dimension once correlation is 0.6 or higher on the golden set; until then use it only for ranking.
- Production: operator edit rate (HTER-style), share of buffs published without edit, edit time, edit reason distribution, viewer reports per 1,000 buffs.

### Cadence

- Every prompt, model or glossary change: re-run the golden set through validators and the judge (minutes).
- Every model switch or monthly: human rating of a 50-item sample per locale.
- Quarterly: full human pass and model bake-off (M9).

## 5. Judge prompt draft

Run with temperature 0, structured JSON output, and a model from a different family than the generator. Fill the per-locale blocks from the style sheet.

```text
You are a senior {LANGUAGE_NAME} sports editor and native speaker, reviewing interactive
questions ("buffs") shown to football fans on their phones during a live match.
You judge the {LANGUAGE_NAME} text on its own terms. There may be no English source;
do not reward closeness to English.

LOCALE STYLE RULES
{STYLE_SHEET}            # address form, quotes, number/minute format, banned calques

FOOTBALL GLOSSARY (preferred terms; inflect as the sentence requires)
{GLOSSARY_ENTRIES}

ENTITY FORMS (use exactly these forms)
{ENTITY_TABLE}           # team/player -> nom, gen, dat, acc, loc, ...

BUFF SPECIFICATION (ground truth)
{SPEC_JSON}              # type, subject, options meaning, correct answer, match state

UI LIMITS
question <= {Q_MAX} chars, each option <= {OPT_MAX} chars, reveal <= {R_MAX} chars

BUFF TO REVIEW
question: {QUESTION}
options: {OPTIONS}
correct option (if any): {CORRECT}
reveal: {REVEAL}

TASK
1. List every error as a span. For each give: the exact text span, the category
   (grammar | spelling_diacritics | agreement_case | unnatural_calque | terminology |
   register_address | faithfulness | ambiguity | length_ui | other), the severity
   (minor | major | critical), and a corrected version of the span.
   Critical = misleads the fan or makes the answer key wrong.
   Major = a native would notice immediately and it hurts trust.
   Minor = a native might not notice.
2. Score each dimension 1-5 using these anchors:
   grammar: 5 no errors, 3 one clear error, 1 ungrammatical throughout.
   naturalness: 5 indistinguishable from a local sports editor, 3 clearly translated,
                1 word-for-word English.
   terminology: 5 terms local fans use, 3 one wrong/English term, 1 confusing.
   faithfulness: 5 exactly matches the spec, 3 a wrong detail but correct answer key,
                 1 wrong answer key, wrong team/player, or flipped negation.
   tone: 5 fits a live fan moment, 3 reads like a form, 1 off-putting.
   ui_fit: 5 well within limits and parallel options, 3 near limits or uneven,
           1 over limits.
   Score from the errors you listed. Do not give 5 on a dimension that has a
   listed error in a matching category.
3. Write one improved version of the whole buff that fixes every error and keeps
   the same meaning and answer key.

Return only JSON:
{
  "errors": [{"span": "", "category": "", "severity": "", "fix": ""}],
  "scores": {"grammar": 0, "naturalness": 0, "terminology": 0,
             "faithfulness": 0, "tone": 0, "ui_fit": 0},
  "publishable": true,
  "improved": {"question": "", "options": [], "reveal": ""}
}
"publishable" is false if any critical error exists or any score is below 3.
```

Notes on use:
- The "improved" field doubles as the self-refine step (M7), so one call can judge and repair. Re-validate the improved version with M6 before using it.
- For offline comparisons, hide which system produced each buff and randomize order.
- Ask for errors before scores; span-first prompting is what made GEMBA-MQM more reliable than single-score prompting at segment level.

## 6. Suggested build order

1. Week 1: golden set specs and native reference buffs for all three locales; native seed of style sheet and glossary; validators (M6). Baseline today's translate pipeline on the golden set so there is a number to beat.
2. Week 2: native-first spec-driven prompts (M1, M2) and entity form tables for the leagues in scope (M3); model bake-off per locale (M9); judge prompt and calibration (M8).
3. Week 3: over-generate and rerank (M5); templates for the top buff shapes (M4); edit capture and reason taps in the admin (M11).
4. After launch: retrieval few-shot (M12), self-refine on flagged buffs (M7), engagement A/B (M16). Revisit fine-tuning (M13) once there are thousands of approved pairs per locale.

## 7. Open questions for the team

- Address form per locale (formal jūs/Jūs vs informal tu/sina) for a fan game: needs a native product call.
- Lithuanian morphology tool choice: not verified in this pass.
- Latvian and Estonian Microsoft style guide specifics: PDFs could not be read with the tools used; a native should extract the relevant sections.
- Do Baltic buffs need to mirror English buffs one-to-one (shared answer keys, shared leaderboards), or can each locale pick its own moments? The spec design in M1 supports both.
