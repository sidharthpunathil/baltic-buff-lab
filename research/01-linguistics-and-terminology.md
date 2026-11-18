# 01 · Linguistics and terminology for Baltic buffs (lt, lv, et)

Research date: 2026-11-17. Scope: what breaks when an LLM or MT system writes short poll, quiz and prediction copy in Lithuanian, Latvian and Estonian, and which sports terms native broadcasters actually use.

How to read this file:

- **[V]** means I saw it in the cited source during this pass.
- **[U]** means unverified: textbook grammar I am confident about but did not re-confirm from a fetched page, or a judgment call. Treat [U] as a review item for a native editor.
- All example buff questions in section 3 are **my drafts** unless a URL is given. None has been reviewed by a native speaker.
- Machine-readable glossaries: `baltic-buff-lab/data/glossary/{lt,lv,et}.json`. The tables in section 2 are generated from the same data.

Note on the client: Go3 is run by what Estonian Wikipedia now calls TV3 Group, the former All Media Baltics ([et.wikipedia.org/wiki/Go3](https://et.wikipedia.org/wiki/Go3)) [V].

---

## 0. Fact-check of the other model's claims

| # | Claim | Verdict and evidence |
|---|---|---|
| a | LT and LV have 7 cases, ET has 14 | **Mostly right, needs nuance.** ET 14 is the standard count [V] ([et.wikipedia: Eesti keele grammatika](https://et.wikipedia.org/wiki/Eesti_keele_grammatika); EKI teatmik lists 14 declension types, a different thing, so don't conflate them). LV is taught as 7 cases incl. instrumental and vocative [V] ([skrivanek.lv](https://skrivanek.lv/kas-ir-locijums/)), but the instrumental has no endings of its own in modern Latvian: it appears only after *ar* and borrows accusative sg / dative pl forms ([pilsoniba.lv](https://pilsoniba.lv/en/gramatika/02-03-locijumu-sistema)) [V]. For generation purposes LV behaves like 5 distinct case forms plus vocative. LT 7 including vocative (*šauksmininkas*) [U, standard grammar]. |
| b | LT krepšinis = basketball, įvartis = goal, baudinys = penalty; ET korvpall, värav, suluseis = offside | **All correct.** Each seen in current native press [V]: krepšinis ([LRT](https://lrt.lt/naujienos/sportas/10/3113027/po-nesekmes-juskaite-neslepe-apmaudo-dareme-kvailu-klaidu-ir-nepagavome-ritmo)), įvartis and baudinys ([15min](https://15min.lt/sportas/naujiena/futbolas/oficialus-cepo-debiutas-su-nezinomybes-prieskoniu-tylu-kaip-24-2806736)), korvpall ([ERR](https://sport.err.ee/1610196871)), suluseis ([soccernet.ee](https://soccernet.ee/artikkel/videokohtunik-var-i-puudumine-roovis-transilt-varava-paides-jai-markamata-suluseis)). Missing caveat: in LT *baudos smūgis* is a free kick, not a penalty; in ET *karistuslöök* is a free kick, not a penalty. Both are the most likely MT errors. | |
| c | A "Stonkus dictionary" for LT sports terms exists | **Correct.** *Sporto terminų žodynas*, Lietuvos kūno kultūros akademija, compiled by Stanislovas Stonkus, Kaunas: LKKA, 2002 [V] ([LSU library record](https://virtualibiblioteka.lka.lt/discovery/fulldisplay/alma990000051943108479/370LABT_LKA:LKA)). It is also a cited source inside the VLKK term bank ([terminai.vlkk.lt](https://terminai.vlkk.lt/paieska?search=dribble&zodzio_dalis=0&kalba=2&kaip0=on&sritys=&statusas=0&rykiavimas=0)) [V]. It is a 2002 academic dictionary, so check modern press usage before trusting it for broadcast tone. |
| d | LSPA materials exist for LV sports terms | **Correct.** Uldis Švinks, *Sporta vārdnīca angļu–latviešu*, Rīga 2013, written for Latvijas Sporta pedagoģijas akadēmija (LSPA) students; 521 pages, now hosted by RSU [V] ([PDF](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf)). LSPA itself was merged into Rīga Stradiņš University in 2024 ([lv.wikipedia](https://lv.wikipedia.org/wiki/Latvijas_Sporta_pedago%C4%A3ijas_akad%C4%93mija)) [V]. I used it heavily for the LV glossary. | |
| e | "Even strong models produce lexical hallucinations ~1 in 20 words" | **Real figure, overgeneralized.** Source: Kapočiūtė-Dzikienė, Bergmanis, Pinnis, *Localizing AI: Evaluating Open-Weight Language Models for Languages of Baltic States*, NoDaLiDa 2025 ([arXiv 2501.03952](https://arxiv.org/abs/2501.03952); [ACL](https://aclanthology.org/2025.nodalida-1.30.pdf)) [V]. The abstract says errors in "at least 1 in 20 words for all **open-weight** multilingual LLMs". It is about open-weight models, not "even strong models" in general. Still a good reason to keep a glossary and a native check in the loop. |

Other model errors I'd expect, based on this pass:

- LV offside is **aizmugure** [V], not *aizsegs*. Several sportacentrs.com reports ("atradās aizmugurē", "aizmugures dēļ vārti netika ieskaitīti") and the LSPA dictionary agree ([sportacentrs](https://sportacentrs.com/futbols/spanija/26102025-real_madrid_notikumiem_bagata_klasika_bei)).
- LT does **not** add an ending to *Messi*: press writes **Lionelis Messi**, adapting the first name only ([15min](https://www.15min.lt/sportas/naujiena/futbolas/eros-pabaiga-lionelis-messi-deda-taska-rinktiniu-futbole-24-2754108)) [V]. "Messis" and "Ronaldas" are wrong.
- LV does write **Lionels Mesi** and **Krištianu Ronaldu** [V] ([LSM](https://www.lsm.lv/sports/futbols?p=146)).
- ET keeps the original spelling and adds case endings, but the apostrophe is **not** automatic. Modern EKI rule: use it only when spelling and pronunciation clash (*Jane'il*, *Godot'd*) or for some one-syllable names [V] ([EKI teatmik: võõrnimede käänamine](https://eki.ee/teatmik/voornimede-kaanamine)). So soccernet writes *Messist ja Ronaldost* with no apostrophe [V] ([soccernet](https://soccernet.ee/artikkel/metsa-ja-heina-tiimikaaslastest-premium-liigas-manginud-meesteni-kes-soidavad-mm-ile)).

---

## 1. Grammar pitfalls that break short buff copy

### 1.0 Shared across all three

**Diacritics.** The single most visible failure. Models fall back to ASCII (`Zalgiris`, `varti`, `voit`) or swap look-alikes. Character sets to validate:

- LT: ą č ę ė į š ų ū ž (and capitals)
- LV: ā č ē ģ ī ķ ļ ņ š ū ž
- ET: õ ä ö ü š ž

Two traps that a regex won't catch on its own: ET **õ vs ö** (*lõi* "scored" vs nonsense *löi*), and LV long vowels, where dropping a macron changes the word or makes it look illiterate. Recommended check: reject any output containing characters outside `[A-Za-z0-9 punctuation] + language set`, and flag outputs with zero diacritics over 40 characters (almost impossible in natural lt/lv/et text) [U, heuristic].

**Register: tu, not jūs.** Go3's own copy in all three markets leans informal singular:

- LT: "Go3 – televizija sukurta **tau**. **Žiūrėk** ... **Išbandyk** Go3 jau šiandien!" ([apie.go3.lt](https://apie.go3.lt/ziurek)) [V]. The sports landing page still uses formal "Žiūrėkite ... Go3 – jūsų telefone" ([go3.lt/sport_tv](https://go3.lt/sport_tv)) [V], so the brand is mixed, but app and marketing CTAs go informal.
- LV: "**Skaties** jebkurā ierīcē. **Izmēģini** Go3 tūlīt!", account page "**Tavs** maksas abonements", Play Store "Go3 **Tu** atradīsi..." ([go3.lv](https://www.go3.lv/); [Google Play](https://play.google.com/store/apps/details?id=lv.go3.android.mobile&hl=lv)) [V]. The homepage also opens with plural "Baudiet" once.
- ET: "**Naudi** ... ja **vaata**", help pages "Kui **sul** ei olnud...", "sobib **sulle**" ([go3.ee](https://go3.ee/); [abi.go3.ee](https://abi.go3.ee/article/go3-sport-ja-extra-sport/)) [V].

Recommendation: informal singular in every buff (LT *tu / tavo / spėk*, LV *tu / tavs / min*, ET *sina / sinu / arva*). Never mix registers inside one buff. LT models often capitalize polite *Jūs*; that reads like a bank letter.

**Team and club names.** The three languages handle them differently, and getting this wrong is an instant tell:

- LT: foreign club names go in „…“ quotes and **stay undeclined**: „Real Madrid“, „Manchester City“, „Barcelona“ ([15min](https://15min.lt/sportas/naujiena/futbolas/isrinktas-geriausiu-pasaulio-futbolininku-vienuoliktukas-kane-ui-vietos-neliko-24-2802322)) [V]. Lithuanian-language club names are quoted **and declined**: „Šiauliai“ palaužė „Nevėžį“ ([LRT](https://lrt.lt/naujienos/sportas/10/3108072/dramatiskoje-kovoje-siauliai-palauze-nevezi)) [V]. City goes before as a genitive: Kauno „Žalgiris“, Kėdainių „Nevėžį“. When a foreign name must take a case, add a declinable head noun: *„Barcelona“ komandai*, *„Real“ klubo*. Country names are ordinary declined nouns: *Lietuva → Lietuvos, Lietuvai*.
- LV: club names in "…" quotes, undeclined, with a genitive city in front: *Saloniku "Aris"*, *Ņujorkas "Rangers"*, *"Barcelona" labā* ([diena.lv](https://diena.lv/raksts/sports/basketbols/_rigas-zelli_-eirokausa-maca-parliecinosi-zaude-_aris_-komandai); [LSM](https://lsm.lv/sports/hokejs)) [V]. Press also uses the declined city as a metonym: *Badalonas uzvarā*, *Memfisas uzvarā*, *Barselonas futbola zvaigzne* ([rigatv](https://rigatv.com/lv/raksts/latvietis-vavers-guva-15-punktus-memfisas-uzvara-par-luivilu-7745511); [la.lv](https://la.lv/panamas-skandals-dokumentos-mineti-lembergi-gulbji-kirsons-un-jaunais-airbaltic-investors)) [V]. Latvian-named clubs decline normally (*"Rīgas zeļļi"*).
- ET: no quotes, names fully declined like ordinary nouns: *Transi seljatanud Kuressaare*, *Unitedi vastu*, *Levadia mees* [V]. City parts are Estonianized: *Pariisi Saint-Germain*, *Milano Inter*, *Peterburi Zeniit* ([soccernet](https://soccernet.ee/artikkel/eesti-kohtub-argentinaga-staadionil-kus-messi-on-loonud-seitse-varavat)) [V].

**Score and number formatting.**

- Scores: colon with no spaces in LT/LV/ET sports press (2:0, 83:76, 1:2) [V across sources]. EKI's formal rule writes the ratio colon with spaces (*võit 75 : 72*) [V] ([EKI arvukirjutus](https://teatmik.eki.ee/teatmik/arvukirjutus)), but press uses 2:0. Use the press form.
- Decimal comma in all three: LT *3,17 tikėtino įvarčio* [V], LV *14,0 punktus*, *93,55%* [V], ET *2,4 mln* [V, EKI].
- Thousands grouped with a space: LT *12 325* ([VLKK](https://vlkk.lt/konsultacijos/10644-skaiciai-grupavimas-tarpas)) [V], ET *6 748 422* [V, EKI].
- Percent: VLKK wants a space, *1 %* ([VLKK](https://vlkk.lt/konsultacijos/7369-procentai-tarpas)) [V]; LV and ET press write *93,55%* without one [V for LV]. ET EKI shows *0,01%* [V].
- Time: ET everyday text uses a dot, *9.30*, and a bare hour for full hours, *kell 19* not *19.00*; ISO colon *19:00* also allowed [V, EKI]. LV press: *pl. 18.20* ([LSM](https://lsm.lv/raksts/sports/futbols/01.10.2026-futbola-izlases-galvenais-treneris-nikolato-mums-sagada-grutibas-panakt-uzlabojumus.a665728)) [V]. LT: *19.30 val.* or *19:30* [U].
- Ordinals take a trailing dot in LV and ET (*643. vārtus*, *24. juuni*) [V]. LT minute ordinals in press: *49 min.*, *119-ąją minutę* [V].

**Quotes.** LT „…“ [V]. ET „…“ in ERR/Õhtuleht [V], with “…” also seen on tv3.ee. LV press uses both "…" and «…» (LSM section titles use «Futbols») [V]. Never emit straight English " in LT.

### 1.1 Lithuanian

1. **Numeral + noun agreement** [U, standard grammar; matches press examples]. 1, 21, 31… take nominative singular (*1 įvartis*, *21 taškas*). 2 to 9 (and 22 to 29…) take nominative plural (*3 įvarčiai*). 10 to 20 and round tens take genitive plural (*10 įvarčių*, *19 taškų*: "pelnė 19 taškų" [V, LRT]). Options like "0–2 įvarčiai" therefore need care: write "Iki 2 įvarčių" / "3 ir daugiau" or avoid the noun.
2. **Plural-only nouns.** *rungtynės* (match), *lygiosios* (draw), *vartai* (goal frame) only exist in the plural [V in press: "sužaidė 207 rungtynes", "lygiosiomis su Surinamu"]. With numbers they take collective numerals: *vienos rungtynės, dvejos rungtynės* [U]. MT often outputs *vienas rungtynės* or *mačas*.
3. **Case after verbs.** Negation flips the object to genitive: *laimės rungtynes* → *nelaimės rungtynių* [U]. Very common MT error in "Will X not score?" options. *Laimėti* takes accusative, *nusileisti* takes dative (*nusileido „Rigas"...* [V]), *įveikti* accusative.
4. **Foreign person names** [V from press]: Lithuanian endings are added to the original spelling when the name ends in a consonant: *Erlingas Haalandas*, *Kylianas Mbappe*, *Davidas Raya*. Names ending in a vowel such as *-i*, *-o*, *-e* usually stay undeclined in press: *Messi*, *Cristiano Ronaldo*, *Mbappe*. Names ending in a silent letter get an apostrophe before the ending: *Kane'ui*, *Jude'as Bellinghamas*, *Lamine'as Yamalis* ([15min](https://15min.lt/sportas/naujiena/futbolas/isrinktas-geriausiu-pasaulio-futbolininku-vienuoliktukas-kane-ui-vietos-neliko-24-2802322); [tv3.lt](https://tv3.lt/naujiena/sportas/paskelbtas-geriausiu-praejusio-sezono-zaideju-11-tukas-sukele-pasipiktinima-n1567352)). VLKK describes three methods: ending after an apostrophe, directly onto the stem, or replacing the stem-final letters ([VLKK gramatinimas page, snippet only; site was Cloudflare-blocked](https://www.vlkk.lt/aktualiausios-temos/svetimvardziai/gramatinimas)). Practical rule: copy the form from 15min/LRT/delfi; don't invent one. Press abbreviates first names as *L. Messi*, *K. Mbappe*, often without a space (*M.Ruzgio*).
5. **Gender agreement.** Women's teams and players need feminine forms: *krepšininkė pelnė*, *rezultatyviausia* [V, LRT]. Participles in options must agree with the team noun: *„Žalgiris" laimėjęs* vs *rinktinė laimėjusi* [U].
6. **Yes/no questions** start with **Ar**: *Ar „Žalgiris" laimės?* [U, standard]. Dropping *ar* is spoken style.
7. **Vocative** for direct address to a player is rare in buffs; avoid.
8. **"Kitas" not "sekantis" for "next".** *Sekantis* in the sense of "next" is a long-standing VLKK-flagged Russianism [U; VLKK's "big errors list" was retired in 2019 per [Skrivanek](https://skrivanek.lt/didziuju-klaidu-sarasas-mire-tegyvuoja-klaidos), but editors still flag it].

### 1.2 Latvian

1. **"Vārti" is plural-only.** One goal = *vieni vārti*; "the only goal" = *vienīgos vārtus* [V, LSM: "Vienīgos vārtus 106. minūtē guva..."]; "scored his 643rd goal" = *guva savus 643. vārtus* [V]. Every adjective and pronoun agrees in plural. "Who will score the next goal?" must be **Kurš gūs nākamos vārtus?** MT output like *nākamo vārtu* or *nākamais vārts* is the most frequent LV football error I'd expect [U, prediction].
2. **Numerals.** Numbers ending in 1 (except 11) take singular, everything else plural (*21 punkts*, *15 punktus*) [U]. After *cik* (how many) use genitive plural: *Cik vārtu...?* [U].
3. **Foreign names are respelled phonetically** and get Latvian endings: *Lionels Mesi*, *Krištianu Ronaldu*, *Manuels Noiers*, *Belingems*, *Kurtuā*, *Mbapē* ([LSM](https://lsm.lv/sports/futbols/bumba-savos-vartos-gaisina-bfc-daugavpils-izredzes-uz-punktu-virsligas-tabula.a327837?p=232); [sportacentrs](https://sportacentrs.com/?mobile=1&page=1879)) [V]. Names ending in -i/-u/-ē stay undeclined. This is the opposite of LT and ET. An LLM keeping "Messi" in LV copy is a visible error. Club and team names do not get respelled ("Barcelona", "Rangers") [V].
4. **Penalty ambiguity.** *Soda sitiens* alone can mean a direct free kick (LSPA lists both senses). Press always says **11 metru soda sitiens** for a penalty, and players say "pendele" in quotes [V]. Use the full form.
5. **Hockey vs football verbs.** Hockey goals are *iemesti* (thrown), football goals *iesisti* (kicked); hockey shots are *metieni*, football shots *sitieni* [V]. Mixing them is a translationese tell.
6. **Yes/no questions** start with **Vai**: *Vai Latvija uzvarēs?* [U, standard].
7. **Vocative**: proper names lose the ending in address (*Kaspar!*) [V, [valodaskonsultacijas.lv](https://www.valodaskonsultacijas.lv/lv/questions/731)]. Avoid addressing players directly.
8. **"Priekš" misuse.** English "for" calqued as *priekš* (*balso priekš komandas*) is the classic LV translationese tell; use dative or *par* (*balso par komandu*) [U].

### 1.3 Estonian

1. **Partitive after numerals.** When the numeral is in the nominative, the noun is partitive singular: *15 kuud*, *11 km*, *5%* ([EKI arvukirjutus](https://teatmik.eki.ee/teatmik/arvukirjutus)) [V]; press: *kolm väravat*, *12 punkti*, *9 punkti* [V]. In other cases the noun agrees with the numeral: *kaheksa lauapalliga*, *viie mänguga* [V, ERR/soccernet]. So "How many goals?" = **Mitu väravat?**, and options "0 / 1–2 / 3 või rohkem" need no noun.
2. **No partitive marker on digits 0 to 4.** EKI: write *Kanal 2*, not *2-t* [V, keeleabi.eki.ee snippet].
3. **Foreign names** keep their spelling and take endings based on pronunciation; apostrophe only when spelling and pronunciation conflict [V, EKI]. *Messist*, *Ronaldost* [V]. Names with a silent final letter (French names especially) are where an editor should decide on the apostrophe [U].
4. **Object case and aspect.** Total object (genitive/nominative) for completed results, partitive for ongoing or negated: *lööb värava* (will score a goal) vs *ei löö väravat* (won't score) [U, standard; press "lasknud endale lüüa vaid ühe värava" V]. Negation always partitive. MT frequently gets this wrong in "Will X score?" yes/no options.
5. **Yes/no questions** start with **Kas**: *Kas Eesti võidab?* [U, standard; seen in ERR headline "kas Eesti saab ka võõrsil Luksemburgist jagu" V].
6. **No grammatical gender**, so no agreement errors there, but there is also no future tense: *Kes võidab?* is "Who will win?" Models sometimes insert *hakkab võitma*, which sounds odd [U].
7. **Free kick vs penalty.** *Karistuslöök* = free kick [V: "skooris otse karistuslöögist"]. Penalty = *penalti* [V]. A literal "penalty kick → karistuslöök" changes the meaning, which is worse than a style slip.
8. **"Poolt" passives.** "The goal was scored by X" → *X-i poolt löödud värav* is the textbook Estonian translationese marker; write *X lõi värava* [U, widely taught EKI advice].
9. **"Arvulises ülekaalus"**, not *arvuliselt ülekaalus* (EKI style guide correction) [V, [EKI ametnik.pdf](https://arhiiv.eki.ee/dict/ametnik/ametnik.pdf)].

---

## 2. Sport priority per country

- **Lithuania:** basketball first (EuroLeague Žalgiris, LKL), then football, ice hockey a distant third. Go3 LT leads its sports page with "krepšinio (Eurolyga)" [V, [go3.lt/sport_tv](https://go3.lt/sport_tv)].
- **Latvia:** ice hockey and basketball, both national-team driven (Deutschland Cup, World Championship; Rīgas zeļļi, VEF). Go3 LV live listings show hockey in prime time [V, [go3.lv/live_tv](https://go3.lv/live_tv)]. Football is smaller.
- **Estonia:** basketball (Bigbank/Kalev, Estonian-Latvian league) and football (Premium liiga, national team in the Nations League) dominate ERR's sports output this month [V, sport.err.ee]. Hockey is minor; the national team plays lower IIHF divisions [V, ERR "Eesti jäähokikoondis ... Rumeeniale"].

Go3 channels carry Estonian, Latvian and Lithuanian commentary on Go3 Sport 1, 2 and 3 [V, [Go3 help](https://pagalba.go3.lt/en/article/what-channels-are-available-in-go3)].

## 2a. Glossary: Lithuanian (lt)

| EN | Native term | Avoid | Sport | Note | Source | Verified |
|---|---|---|---|---|---|---|
| match / game | **rungtynės** | matčas, mačas (colloquial), žaidimas | general | Plural-only noun (pluralia tantum): vienos rungtynės, dvejos rungtynės (collective numerals). 'Mačas' appears in 15min headlines in quotes but is colloquial; use rungtynės in buffs. | [link](https://15min.lt/sportas/naujiena/futbolas/paskutines-metu-rungtynes-lietuva-lichtensteinas-24-2807356) | yes |
| half (football) | **kėlinys** | pusė, puslaikis | football | pirmasis / antrasis kėlinys. Same word is used for hockey periods. | [link](https://15min.lt/sportas/naujiena/futbolas/oficialus-cepo-debiutas-su-nezinomybes-prieskoniu-tylu-kaip-24-2806736) | yes |
| period (ice hockey) | **kėlinys** | periodas | hockey | Antrajame kėlinyje... | [link](https://15min.lt/sportas/naujiena/ziemos-sportas/lietuvos-ledo-ritulininkai-tautu-taures-varzybas-baige-pralaimejimu-estijai-295-2801178) | yes |
| quarter (basketball) | **kėlinys / ketvirtis** |  | basketball | LT basketball press uses kėlinys for quarters; ketvirtis also seen. Not confirmed from a source in this pass. | none | NO |
| overtime | **pratęsimas** | overtaimas, papildomas laikas | general | per pratęsimą (during OT). | [link](https://15min.lt/sportas/naujiena/ziemos-sportas/latvijoje-lietuvos-ledo-ritulininku-taskas-295-2806562) | yes |
| extra time (football) | **pratęsimas** | papildomas laikas | football | Same word as overtime. | [link](https://15min.lt/sportas/naujiena/futbolas/auksini-maca-baudiniu-serijoje-laimejes-plunges-babrungas-iskovojo-kelialapi-i-toplyga-24-2804024) | yes |
| penalty shoot-out | **baudinių serija** | penalų serija, baudos smūgių serija | football | laimėti baudinių serijoje | [link](https://15min.lt/sportas/naujiena/futbolas/auksini-maca-baudiniu-serijoje-laimejes-plunges-babrungas-iskovojo-kelialapi-i-toplyga-24-2804024) | yes |
| penalty kick | **baudinys** | penalas, bausmės smūgis, baudos smūgis | football | 'Baudos smūgis' is a FREE KICK, not a penalty. Realizuoti baudinį = convert a penalty. | [link](https://15min.lt/sportas/naujiena/futbolas/oficialus-cepo-debiutas-su-nezinomybes-prieskoniu-tylu-kaip-24-2806736) | yes |
| penalty spot | **11 metrų žyma** | penalų taškas | football |  | [link](https://15min.lt/sportas/naujiena/futbolas/oficialus-cepo-debiutas-su-nezinomybes-prieskoniu-tylu-kaip-24-2806736) | yes |
| penalty area / box | **baudos aikštelė** | baudos zona | football |  | [link](https://15min.lt/sportas/naujiena/futbolas/skirtingi-grandu-likimai-liverpool-triumfavo-o-chelsea-krito-pries-autsaiderius-24-2801424) | yes |
| free kick | **baudos smūgis** | laisvas smūgis, frikikas | football | tiesioginis / netiesioginis baudos smūgis (LFF rules). | [link](https://lff.lt/files/documents/160/2017m.Futbolo-taisykles.pdf) | yes |
| corner kick | **kampinis (smūgis)** | kornas, kampo smūgis | football | Usually just kampinis: po kampinio, kampiniai 6:2. | [link](https://15min.lt/sportas/naujiena/futbolas/paskutines-metu-rungtynes-lietuva-lichtensteinas-24-2807356) | yes |
| offside | **nuošalė** | ofsaidas | football | atsidūrė nuošalėje (was offside). | [link](https://klaipeda.diena.lt/naujienos/sportas/futbolas/pirmasis-ketvertas-zemaiciams-uzsivere-1780428) | yes |
| VAR review | **VAR peržiūra** |  | football |  | [link](https://klaipeda.diena.lt/naujienos/sportas/futbolas/pirmasis-ketvertas-zemaiciams-uzsivere-1780428) | yes |
| yellow card | **geltonoji kortelė** | geltonas lapelis | football | Press also writes 'geltoną kortelę užsidirbo'. | [link](https://15min.lt/sportas/naujiena/futbolas/skirtingi-grandu-likimai-liverpool-triumfavo-o-chelsea-krito-pries-autsaiderius-24-2801424) | yes |
| red card | **raudonoji kortelė** |  | football | Parallel to geltonoji kortelė; not seen in a fetched source this pass. | none | NO |
| goal (scored) | **įvartis** | golas (slang) | general | įmušti / pelnyti įvartį. 'Vartai' (the goal frame) is plural-only. | [link](https://15min.lt/sportas/naujiena/futbolas/oficialus-cepo-debiutas-su-nezinomybes-prieskoniu-tylu-kaip-24-2806736) | yes |
| to score a goal | **įmušti įvartį / pelnyti įvartį** | padaryti įvartį, skoruoti | general |  | [link](https://15min.lt/sportas/naujiena/futbolas/paskutines-metu-rungtynes-lietuva-lichtensteinas-24-2807356) | yes |
| goalkeeper | **vartininkas** | golkiperis | general | Also 'vartų sargas' in press. | [link](https://15min.lt/sportas/naujiena/ziemos-sportas/lietuvos-ledo-ritulininkai-tautu-taures-varzybas-baige-pralaimejimu-estijai-295-2801178) | yes |
| save (goalkeeper) | **atremti (smūgį / metimą)** | išgelbėti smūgį | general | metimą atrėmė vartininkas (hockey). | [link](https://www.lrt.lt/naujienos/sportas/10/1965357/lietuvos-ledo-ritulio-rinktinei-nepavyko-palauzti-ukrainieciu) | yes |
| shot (football) | **smūgis** | šūvis | football | smūgiai 21:7 | [link](https://15min.lt/sportas/naujiena/futbolas/paskutines-metu-rungtynes-lietuva-lichtensteinas-24-2807356) | yes |
| assist | **rezultatyvus perdavimas** | asistas (slang) | general | Used for basketball and hockey stats. | [link](https://lrt.lt/naujienos/sportas/10/3113027/po-nesekmes-juskaite-neslepe-apmaudo-dareme-kvailu-klaidu-ir-nepagavome-ritmo) | yes |
| substitution | **keitimas** |  | general | Not seen in a fetched source this pass. | none | NO |
| draw | **lygiosios** | lygybė, lygus rezultatas (stiff) | general | Plural-only: baigėsi lygiosiomis. | [link](https://15min.lt/sportas/naujiena/futbolas/egzotiskas-isbandymas-lapkricio-zvarboje-lietuva-surinamas-24-2804940) | yes |
| win / victory | **pergalė; laimėti, nugalėti, įveikti** |  | general |  | [link](https://15min.lt/sportas/naujiena/futbolas/paskutines-metu-rungtynes-lietuva-lichtensteinas-24-2807356) | yes |
| loss / to lose | **pralaimėjimas; pralaimėti, nusileisti** |  | general | baigė pralaimėjimu; nusileido. | [link](https://15min.lt/sportas/naujiena/ziemos-sportas/lietuvos-ledo-ritulininkai-tautu-taures-varzybas-baige-pralaimejimu-estijai-295-2801178) | yes |
| score / result | **rezultatas** |  | general | Score written with colon and no spaces in press: 2:0. | [link](https://15min.lt/sportas/naujiena/futbolas/oficialus-cepo-debiutas-su-nezinomybes-prieskoniu-tylu-kaip-24-2806736) | yes |
| expected goals (xG) | **tikėtini įvarčiai** |  | football | 3,17 tikėtino įvarčio (xG) | [link](https://15min.lt/sportas/naujiena/futbolas/paskutines-metu-rungtynes-lietuva-lichtensteinas-24-2807356) | yes |
| man of the match | **geriausias rungtynių žaidėjas** | rungtynių žmogus (calque) | general | Source shows 'varžybų geriausiais žaidėjais pripažinti'; exact buff phrasing is a draft. | [link](https://silutesnaujienos.lt/lt/r-jocio-tritaskis-sustabde-suduvos-sugrizima) | NO |
| national team | **rinktinė** | nacionalinė komanda (stiff) | general |  | [link](https://15min.lt/sportas/naujiena/futbolas/oficialus-cepo-debiutas-su-nezinomybes-prieskoniu-tylu-kaip-24-2806736) | yes |
| footballer | **futbolininkas** |  | football |  | [link](https://15min.lt/sportas/naujiena/futbolas/paskutines-metu-rungtynes-lietuva-lichtensteinas-24-2807356) | yes |
| basketball | **krepšinis** |  | basketball | Lithuania's number-one sport. | [link](https://lrt.lt/naujienos/sportas/10/3113027/po-nesekmes-juskaite-neslepe-apmaudo-dareme-kvailu-klaidu-ir-nepagavome-ritmo) | yes |
| basketball player | **krepšininkas / krepšininkė** |  | basketball | Gendered: krepšininkė for women. | [link](https://lrt.lt/naujienos/sportas/10/3113027/po-nesekmes-juskaite-neslepe-apmaudo-dareme-kvailu-klaidu-ir-nepagavome-ritmo) | yes |
| three-pointer | **tritaškis** | trijų taškų šūvis | basketball | Stat abbreviation trit. | [link](https://silutesnaujienos.lt/lt/r-jocio-tritaskis-sustabde-suduvos-sugrizima) | yes |
| two-point shot | **dvitaškis** |  | basketball | Stat abbreviation dvit. | [link](https://basketnews.lt/news-259476-jarumbausko-rekordo-pakyleti-siauliai-atsitiese-pries-lkl-sezono-issisokelius.html) | yes |
| free throw | **baudos metimas** | laisvas metimas | basketball | Plural baudų metimai; abbreviation baud. | [link](https://basketnews.lt/news-259476-jarumbausko-rekordo-pakyleti-siauliai-atsitiese-pries-lkl-sezono-issisokelius.html) | yes |
| rebound | **atkovotas kamuolys** | atšokęs kamuolys, rebaundas | basketball | atkovojo 10 kamuolių | [link](https://basketnews.lt/news-259476-jarumbausko-rekordo-pakyleti-siauliai-atsitiese-pries-lkl-sezono-issisokelius.html) | yes |
| steal | **perimtas kamuolys** | pavogtas kamuolys | basketball |  | [link](https://basketnews.lt/news-259476-jarumbausko-rekordo-pakyleti-siauliai-atsitiese-pries-lkl-sezono-issisokelius.html) | yes |
| turnover | **klaida** | praradimas | basketball |  | [link](https://basketnews.lt/news-259476-jarumbausko-rekordo-pakyleti-siauliai-atsitiese-pries-lkl-sezono-issisokelius.html) | yes |
| efficiency rating (PIR) | **naudingumo balai** |  | basketball |  | [link](https://basketnews.lt/news-259476-jarumbausko-rekordo-pakyleti-siauliai-atsitiese-pries-lkl-sezono-issisokelius.html) | yes |
| points | **taškai; pelnyti taškų** |  | basketball | pelnė 19 taškų (gen. pl. after 10+). | [link](https://lrt.lt/naujienos/sportas/10/3113027/po-nesekmes-juskaite-neslepe-apmaudo-dareme-kvailu-klaidu-ir-nepagavome-ritmo) | yes |
| EuroLeague | **Eurolyga** | Euroliga | basketball |  | [link](https://go3.lt/sport_tv) | yes |
| ice hockey | **ledo ritulys** | hokėjus (colloquial) | hockey |  | [link](https://15min.lt/sportas/naujiena/ziemos-sportas/lietuvos-ledo-ritulininkai-tautu-taures-varzybas-baige-pralaimejimu-estijai-295-2801178) | yes |
| hockey player | **ledo ritulininkas** | hokėjistas | hockey |  | [link](https://15min.lt/sportas/naujiena/ziemos-sportas/lietuvos-ledo-ritulininkai-tautu-taures-varzybas-baige-pralaimejimu-estijai-295-2801178) | yes |
| puck | **ritulys** | šaibė (slang) | hockey |  | [link](https://www.lrt.lt/naujienos/sportas/10/1965357/lietuvos-ledo-ritulio-rinktinei-nepavyko-palauzti-ukrainieciu) | yes |
| shot (hockey) | **metimas** | smūgis (football word) | hockey | Hockey and basketball use metimas; football uses smūgis. | [link](https://tv3.lt/naujiena/zmones/is-nausedos-netiketumas-sioje-vietoje-jam-nebuvo-lygiu-n1568346) | yes |
| power play | **dauguma (žaisti daugumoje)** | jėgos žaidimas | hockey | daugumoje sušvelnino rezultatą | [link](https://15min.lt/sportas/naujiena/ziemos-sportas/lietuvos-ledo-ritulininkai-tautu-taures-varzybas-baige-pralaimejimu-estijai-295-2801178) | yes |
| short-handed | **mažuma (žaisti mažumoje)** |  | hockey | Pair of dauguma; not seen in a fetched source. | none | NO |
| penalty minutes | **baudos minutės** |  | hockey |  | [link](https://tv3.lt/naujiena/zmones/is-nausedos-netiketumas-sioje-vietoje-jam-nebuvo-lygiu-n1568346) | yes |
| who will score next? | **Kas pelnys kitą įvartį?** | Kas įmuš sekantį įvartį? | general | Draft. 'Sekantis' in the sense of 'next' is a long-flagged Russianism; use kitas. | none | NO |
| who will win? | **Kas laimės?** |  | general |  | [link](https://www.15min.lt/zmones/naujiena/lietuva/m-1-apklausa-sostines-gatvese-ka-palaiko-zmones-kauno-zalgiri-ar-vilniaus-ryta-1050-2317582) | yes |

## 2b. Glossary: Latvian (lv)

| EN | Native term | Avoid | Sport | Note | Source | Verified |
|---|---|---|---|---|---|---|
| match / game | **spēle; mačs** | mačš, geims | general | Mačs is normal in sports press (dramatiskā mačā). Spēle is the neutral default. | [link](https://sportacentrs.com/futbols/latvijas_izlase/02102026-vartu_konstrukcija_un_adzics_sarugtina_la) | yes |
| half (football) | **puslaiks** | puse | football | pirmajā / otrajā puslaikā | [link](https://lsm.lv/raksts/sports/futbols/17.11.2024-latvijas-futbolisti-aizrautiga-spele-zaude-armeniem-naciju-ligas-grupa-paliek-pedejie-galvenie-notikumi.a576773) | yes |
| period (ice hockey) | **periods** | trešdaļa | hockey | otrā perioda ievadā | [link](https://www.lsm.lv/raksts/sports/hokejs/08.11.2026-latvijas-hokeja-izlase-uzvar-austriju-un-izcina-vacijas-kausu.a670992/) | yes |
| quarter (basketball) | **ceturtdaļa** |  | basketball | Not confirmed from a fetched source this pass. | none | NO |
| overtime / extra time | **papildlaiks** | virslaiks, overtaims | general | LSPA dictionary: overtime = papildlaiks; also seen in LSM (guva uzvaras vārtus papildlaikā). | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| regulation time | **pamatlaiks** |  | general | pirms pamatlaika beigām | [link](https://www.lsm.lv/sports/hokejs/rigas-dinamo-tresaja-perioda-iemet-cetras-ripas-un-parspej-sanktpeterburgas-ska.a327851/?p=322) | yes |
| stoppage time | **kompensācijas laiks** | pievienotais laiks | football | kompensācijas laikā | [link](https://diena.lv/raksts/sports/futbols/latvijas-futbolisti-naciju-liga-zaude-melnkalnei) | yes |
| shoot-out (hockey) | **pēcspēles metieni** | buliti (Russianism) | hockey | Metieni (shots), because hockey uses metiens. | [link](https://www.lsm.lv/sports/hokejs/rigas-dinamo-tresaja-perioda-iemet-cetras-ripas-un-parspej-sanktpeterburgas-ska.a327851/?p=322) | yes |
| penalty shoot-out (football) | **pēcspēles sitieni (11 m)** | penāļu sērija | football | LSPA: penalty kicks = pēcspēles (11 m) sitieni. | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| penalty kick | **11 metru soda sitiens** | soda sitiens (alone: ambiguous), penaltijs | football | Colloquial 'pendele' appears in quotes in LFF and press. Bare 'soda sitiens' can also mean a direct free kick (LSPA), so keep '11 metru'. | [link](https://sportacentrs.com/futbols/latvijas_izlase/25092026-latvijas_izlase_naciju_ligas_jauno_celien) | yes |
| penalty area | **soda laukums** |  | football |  | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| free kick | **brīvsitiens** |  | football | LSPA lists 'soda sitiens' as rare for direct free kick; brīvsitiens is the clear term. | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| corner kick | **stūra sitiens** | korners | football | izpildīt stūra sitienus | [link](https://lsm.lv/raksts/sports/futbols/17.11.2024-latvijas-futbolisti-aizrautiga-spele-zaude-armeniem-naciju-ligas-grupa-paliek-pedejie-galvenie-notikumi.a576773) | yes |
| offside | **aizmugure** | aizsegs, ofsaids | football | atradās aizmugurē; vārti aizmugures dēļ netika ieskaitīti. LSPA confirms offside = aizmugure. | [link](https://sportacentrs.com/futbols/spanija/26102025-real_madrid_notikumiem_bagata_klasika_bei) | yes |
| offside (ice hockey) | **zona (ieslidošana zonā pirms ripas)** |  | hockey | LSPA wording; commentators may differ. | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| icing | **pārmetiens** |  | hockey |  | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| yellow card | **dzeltenā kartīte** | dzeltenā karte | football | nopelnīja dzelteno kartīti | [link](https://diena.lv/raksts/sports/futbols/latvijas-futbolisti-naciju-liga-zaude-melnkalnei) | yes |
| red card | **sarkanā kartīte** | sarkanā karte | football |  | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| goal (scored) | **vārti** | vārts (singular does not exist for this sense), gols | general | Plural-only. One goal = vieni vārti; 'next goal' = nākamie vārti; 'scored three goals' = guva trīs vārtus. | [link](https://www.lsm.lv/sports/futbols?p=136) | yes |
| to score a goal | **gūt vārtus; iesist / iemest vārtus** | skorot | general | iesist (football), iemest (hockey/handball). | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| goalkeeper | **vārtsargs** | golkīpers | general |  | [link](https://www.lsm.lv/sports/hokejs?p=38) | yes |
| save | **atvairīt (sitienu / metienu)** | izglābt sitienu | general | atvairīja 24 metienus (hockey). | [link](https://www.lsm.lv/sports/hokejs?p=38) | yes |
| assist | **rezultatīva piespēle** | asists | general |  | [link](https://diena.lv/raksts/sports/basketbols/latvijas-basketbolistes-eiropas-cempionata-kvalifikacijas-otro-posmu-sak-ar-parliecinosu-uzvaru) | yes |
| substitution | **spēlētāju maiņa** |  | general |  | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| draw | **neizšķirts** | izlīdzinājums | general | nospēlēja neizšķirti; rezultatīvs neizšķirts 2:2. | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| win / beat | **uzvara; uzvarēt, pārspēt, pieveikt** |  | general |  | [link](https://diena.lv/raksts/sports/hokejs/latvijas-hokejisti-vacijas-kausa-parspej-austriju-un-izcina-pirmo-vietu) | yes |
| lose | **zaudēt; zaudējums; piekāpties** |  | general | piekāpjas Melnkalnei (dat.). | [link](https://sportacentrs.com/futbols/latvijas_izlase/02102026-vartu_konstrukcija_un_adzics_sarugtina_la) | yes |
| final score | **galīgais rezultāts** |  | general |  | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| man of the match | **spēles vērtīgākais spēlētājs** | mača cilvēks (calque) | general |  | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| hat-trick | **hettriks** |  | general | LSM glosses as 'trīs vārtus jeb "hat-trick"'. | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| national team | **izlase; valstsvienība** | nacionālā komanda | general |  | [link](https://www.lsm.lv/raksts/sports/hokejs/08.11.2026-latvijas-hokeja-izlase-uzvar-austriju-un-izcina-vacijas-kausu.a670992/) | yes |
| footballer | **futbolists** |  | football |  | [link](https://lsm.lv/raksts/sports/futbols/17.11.2024-latvijas-futbolisti-aizrautiga-spele-zaude-armeniem-naciju-ligas-grupa-paliek-pedejie-galvenie-notikumi.a576773) | yes |
| basketball | **basketbols** |  | basketball |  | [link](https://diena.lv/raksts/sports/basketbols/latvijas-basketbolistes-eiropas-cempionata-kvalifikacijas-otro-posmu-sak-ar-parliecinosu-uzvaru) | yes |
| basketball player | **basketbolists / basketboliste** |  | basketball |  | [link](https://diena.lv/raksts/sports/basketbols/latvijas-basketbolistes-eiropas-cempionata-kvalifikacijas-otro-posmu-sak-ar-parliecinosu-uzvaru) | yes |
| three-pointer | **trīspunktnieks; tālmetiens** | trīspunktu šāviens | basketball | 2 no 5 trīspunktniekiem | [link](https://rigatv.com/lv/raksts/latvietis-vavers-guva-15-punktus-memfisas-uzvara-par-luivilu-7745511) | yes |
| two-point shot | **divu punktu metiens** |  | basketball |  | [link](https://rigatv.com/lv/raksts/latvietis-vavers-guva-15-punktus-memfisas-uzvara-par-luivilu-7745511) | yes |
| free throw | **soda metiens** | brīvmetiens (rare in press) | basketball | 3 no 3 soda metieniem | [link](https://rigatv.com/lv/raksts/latvietis-vavers-guva-15-punktus-memfisas-uzvara-par-luivilu-7745511) | yes |
| rebound | **atlēkusī bumba** | rebaunds | basketball | izcīnīt atlēkušās bumbas | [link](https://sportacentrs.com/basketbols/eirokausi/13102026-lomaza_komandas_trenerim_un_speletajam_pi) | yes |
| steal | **pārtverta bumba** |  | basketball |  | [link](https://www.lsm.lv/raksts/sports/basketbols/02.04.2023-basko-metiens-priekspedeja-sekunde-atnes-ttt-riga-basketbolistem-cempiontitulu-baltijas-liga.a503364/) | yes |
| blocked shot | **bloķēts metiens** |  | basketball |  | [link](https://diena.lv/raksts/sports/basketbols/latvijas-basketbolistes-eiropas-cempionata-kvalifikacijas-otro-posmu-sak-ar-parliecinosu-uzvaru) | yes |
| dunk | **bumbas ietriekšana grozā** | danks (slang) | basketball |  | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| points | **punkti; gūt punktus** |  | basketball | guva 15 punktus | [link](https://rigatv.com/lv/raksts/latvietis-vavers-guva-15-punktus-memfisas-uzvara-par-luivilu-7745511) | yes |
| ice hockey | **hokejs** | ledus hokejs (redundant) | hockey | Latvia's top spectator sport alongside basketball. | [link](https://www.lsm.lv/sports/hokejs?p=38) | yes |
| hockey player | **hokejists** |  | hockey |  | [link](https://lsm.lv/sports/hokejs) | yes |
| puck | **ripa** | šaiba (Russianism) | hockey |  | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| shot (hockey) | **metiens** | sitiens (football word) | hockey |  | [link](https://diena.lv/raksts/sports/hokejs/latvijas-hokejisti-vacijas-kausa-parspej-austriju-un-izcina-pirmo-vietu) | yes |
| power play | **vairākums (spēlēt vairākumā)** | jaudas spēle | hockey | iemesti trīs vārti vairākumā | [link](https://www.lsm.lv/raksts/sports/hokejs/08.11.2026-latvijas-hokeja-izlase-uzvar-austriju-un-izcina-vacijas-kausu.a670992/) | yes |
| short-handed | **mazākums (spēlēt mazākumā)** |  | hockey | mazākumā gūti vārti = short-handed goal | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| empty net | **spēle bez vārtsarga; tukši vārti** |  | hockey | LSPA gives 'spēle bez vārtsarga'; 'tukšos vārtos' is common in press but not confirmed here. | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | NO |
| faceoff | **iemetiens** |  | hockey |  | [link](https://rsu.lv/sites/default/files/imce/Bibliot%C4%93ka/Resursi/sporta_vardnica_angliski.pdf) | yes |
| who will score next? | **Kurš gūs nākamos vārtus?** | Kurš gūs nākamo vārtu? | general | Draft. Vārti is plural-only, so the adjective is plural too. | none | NO |
| who will win? | **Kurš uzvarēs?** | Kas uzvarēs? (acceptable but less idiomatic for a person/team pick) | general |  | [link](https://strawpoll.com/GPgV3E1qzZa/results) | yes |

## 2c. Glossary: Estonian (et)

| EN | Native term | Avoid | Sport | Note | Source | Verified |
|---|---|---|---|---|---|---|
| match / game | **mäng; kohtumine; matš** |  | general | All three appear in soccernet/ERR. Mäng is the safe default. | [link](https://soccernet.ee/artikkel/henn-tahame-aasta-lopetada-samasuguse-meeskonnana-keda-on-alates-suvest-naha-olnud) | yes |
| half (football) | **poolaeg** | pool | football | avapoolaeg (first half), teine poolaeg. | [link](https://soccernet.ee/artikkel/vaata-jarele-vendade-penalti-juhtis-paide-unitedi-vastu-voidule) | yes |
| period (ice hockey) | **periood** | kolmandik (rare) | hockey | avaperiood = first period | [link](https://sport.err.ee/1610188915/eesti-jaahokikoondis-viskas-otsustaval-perioodil-rumeeniale-kolm-varavat) | yes |
| quarter (basketball) | **veerandaeg** |  | basketball | Standard term; not confirmed in a fetched source this pass. | none | NO |
| overtime (basketball / hockey) | **lisaaeg** | üleaeg | general | teisel lisaajal võitnud | [link](https://sport.err.ee/1610038555/teisel-lisaajal-voitnud-kalev-cramo-viis-finaalseeria-otsustavasse-mangu) | yes |
| stoppage time | **lisaminutid** |  | football | lisaminutite võiduvärav | [link](https://soccernet.ee/artikkel/videokohtunik-kontrollitud-hupe-voi-porge-lisaminutite-voiduvarav-tekitas-suure-segaduse) | yes |
| penalty kick | **penalti** | karistuslöök (= FREE KICK), 11 m karistuslöök (formal, rare in press) | football | Biggest trap: karistuslöök means free kick in Estonian press. | [link](https://soccernet.ee/artikkel/vaata-jarele-vendade-penalti-juhtis-paide-unitedi-vastu-voidule) | yes |
| penalty shoot-out | **penaltiseeria; (pääses) penaltitega** |  | football | Source shows 'pääses penaltitega'; 'penaltiseeria' is common but not seen in a fetched page. | [link](https://soccernet.ee/artikkel/loe-jarele-flora-jai-lopuminutitel-edust-ilma-aga-paases-penaltitega-jargmisesse-ringi) | yes |
| penalty area | **karistusala** | penaltikast (slang) | football |  | [link](https://sport.err.ee/1610155444/eesti-jalgpallikoondis-teenis-rahvuste-liigas-esimese-voidu) | yes |
| free kick | **karistuslöök** | vabalöök (only for indirect free kick, rarely used) | football | skooris otse karistuslöögist | [link](https://soccernet.ee/artikkel/vaata-jarele-transi-seljatanud-kuressaare-astus-suure-sammu-pusimajaamise-suunas) | yes |
| corner kick | **nurgalöök** | korner | football |  | [link](https://soccernet.ee/artikkel/vaata-jarele-vendade-penalti-juhtis-paide-unitedi-vastu-voidule) | yes |
| offside | **suluseis** | ofsaid | football | Confirmed: the other LLM was right on this one. | [link](https://soccernet.ee/artikkel/videokohtunik-var-i-puudumine-roovis-transilt-varava-paides-jai-markamata-suluseis) | yes |
| VAR / video referee | **VAR; videokohtunik** |  | football |  | [link](https://soccernet.ee/artikkel/videokohtunik-var-i-puudumine-roovis-transilt-varava-paides-jai-markamata-suluseis) | yes |
| yellow card | **kollane kaart** | kollane kaardike | football |  | [link](https://soccernet.ee/artikkel/videokohtunik-var-i-puudumine-roovis-transilt-varava-paides-jai-markamata-suluseis) | yes |
| red card | **punane kaart** |  | football | jäi kümnekesi = was down to ten men | [link](https://soccernet.ee/artikkel/loe-jarele-harju-voitis-kodus-kindlalt-transi-ning-lopetas-voidupoua) | yes |
| goal (scored) / goal frame | **värav** | gool (slang) | general | Same word for the frame and the goal scored. | [link](https://soccernet.ee/artikkel/henn-tahame-aasta-lopetada-samasuguse-meeskonnana-keda-on-alates-suvest-naha-olnud) | yes |
| to score a goal | **lööma väravat; skoorima** | väravat tegema | general | Hockey: viskama väravat (viskas kolm väravat). | [link](https://soccernet.ee/artikkel/vaata-jarele-transi-seljatanud-kuressaare-astus-suure-sammu-pusimajaamise-suunas) | yes |
| goalkeeper | **väravavaht** | kipper (slang) | general |  | [link](https://sport.err.ee/1610189461/eesti-varavavaht-meil-oli-palju-noori-aga-suutsime-ikka-taset-sailitada) | yes |
| save | **tõrjuma** | päästma lööki | general | Väravavaht tõrjus löögi. | [link](https://sport.err.ee/1610155444/eesti-jalgpallikoondis-teenis-rahvuste-liigas-esimese-voidu) | yes |
| shot (football) | **pealelöök; löök** |  | football |  | [link](https://sport.err.ee/1610155639/voiduvarava-autor-peetson-kodustaadionil-voit-mis-saaks-parem-olla) | yes |
| header | **pealöök** |  | football |  | [link](https://soccernet.ee/artikkel/vaata-jarele-flora-ei-suutnud-end-harju-laviini-alt-valja-kaevata) | yes |
| assist | **resultatiivne sööt** | assist (slang) | general |  | [link](https://sport.err.ee/1610196493) | yes |
| substitution / substitute | **vahetus; vahetusmängija** |  | general | vahetusest sekkunud = came on as a sub | [link](https://soccernet.ee/artikkel/loe-jarele-harju-voitis-kodus-kindlalt-transi-ning-lopetas-voidupoua) | yes |
| draw | **viik** | viigiline tulemus (stiff) | general | leppisid väravateta viiki | [link](https://soccernet.ee/artikkel/vaata-jarele-kuressaare-ja-kalju-leppisid-varavateta-viiki) | yes |
| win / to beat | **võit; võitma, alistama** |  | general | alistas Luksemburgi | [link](https://sport.err.ee/1610195209/vaata-otse-kas-eesti-saab-ka-voorsil-luksemburgist-jagu) | yes |
| loss / to lose | **kaotus; kaotama** |  | general |  | [link](https://soccernet.ee/artikkel/vaata-jarele-eesti-u21-koondis-kaotas-ka-valiksarja-viimase-mangu) | yes |
| national team | **koondis** | rahvusmeeskond | general |  | [link](https://soccernet.ee/artikkel/henn-tahame-aasta-lopetada-samasuguse-meeskonnana-keda-on-alates-suvest-naha-olnud) | yes |
| football | **jalgpall** | futbol | football |  | [link](https://soccernet.ee/artikkel/henn-tahame-aasta-lopetada-samasuguse-meeskonnana-keda-on-alates-suvest-naha-olnud) | yes |
| basketball | **korvpall** |  | basketball | Confirmed: the other LLM was right. | [link](https://sport.err.ee/1610196871) | yes |
| three-pointer | **kolmepunktivise; (colloq.) kolmene** | kolmepunktiline löök | basketball | ERR stat line: 'kolmesed 1/3'. | [link](https://sport.err.ee/1610196871) | yes |
| two-pointer | **kahepunktivise; (colloq.) kahene** |  | basketball | 'kahesed 4/4' | [link](https://sport.err.ee/1610196871) | yes |
| free throw | **vabavise** | karistusvise | basketball | 'vabavisked 1/2' | [link](https://sport.err.ee/1610196871) | yes |
| rebound | **lauapall** | tagasipõrge | basketball | võttis kolm lauapalli | [link](https://sport.err.ee/1610196871) | yes |
| points | **punktid; viskama punkte** |  | basketball | viskas 12 punkti (partitive sg after numeral) | [link](https://sport.err.ee/1610196871) | yes |
| double-double | **kaksikduubel** |  | basketball |  | [link](https://sport.err.ee/1610196493) | yes |
| ice hockey | **jäähoki** | hoki (colloquial, fine in headlines) | hockey |  | [link](https://sport.err.ee/1610188915/eesti-jaahokikoondis-viskas-otsustaval-perioodil-rumeeniale-kolm-varavat) | yes |
| puck | **litter** | seib | hockey | saatis litri väravasse | [link](https://sport.err.ee/1610188915/eesti-jaahokikoondis-viskas-otsustaval-perioodil-rumeeniale-kolm-varavat) | yes |
| power play | **arvuline ülekaal (mängima arvulises ülekaalus)** | arvuliselt ülekaalus | hockey | EKI's style guide corrects 'arvuliselt ülekaalus' to 'arvulises ülekaalus'. | [link](https://arhiiv.eki.ee/dict/ametnik/ametnik.pdf) | yes |
| short-handed | **vähemus (mängima vähemuses)** |  | hockey | Source shows football 'jättis Transi vähemusse'; hockey usage not confirmed. | [link](https://soccernet.ee/artikkel/loe-jarele-harju-voitis-kodus-kindlalt-transi-ning-lopetas-voidupoua) | NO |
| shot (hockey) | **pealevise** | pealelöök (football word) | hockey | Hockey and basketball 'throw' (vise), football 'kick' (löök). | none | NO |
| who will score next? | **Kes lööb järgmise värava?** | Kes skoorib järgmisena värava? | general | Draft. Hockey variant: Kes viskab järgmise värava? | none | NO |
| who will win? | **Kes võidab?** |  | general | TV3 Estonia uses 'Kes võidab “Ajujahi” saate?' | [link](https://tv3.ee/tv3-kanalileht/ajujaht) | yes |
| how will the match end? | **Kuidas mäng lõpeb?** |  | general | Draft; options: Eesti võit / Viik / Läti võit. | none | NO |

---

## 3. Example buffs

### 3.0 Real examples found

I found very little native poll copy in fetchable form; Go3's own pages are behind a Cloudflare challenge, and news portals render polls client-side. What I did find:

- LT: "Kas laimės" is the stock "who will win" phrasing, e.g. in a 15min street poll on Žalgiris vs Rytas ([15min](https://www.15min.lt/zmones/naujiena/lietuva/m-1-apklausa-sostines-gatvese-ka-palaiko-zmones-kauno-zalgiri-ar-vilniaus-ryta-1050-2317582)) and as the market label on Lithuanian Žalgiris prediction pages [V].
- LV: "Kurš uzvarēs …?" as a poll title ([StrawPoll](https://strawpoll.com/GPgV3E1qzZa/results)) and podcast hook "KURŠ UZVARĒS BALLON D'OR" [V].
- ET: TV3 Estonia (same group as Go3): "Kes võidab “Ajujahi” saate?" ([tv3.ee](https://tv3.ee/tv3-kanalileht/ajujaht)) [V]. ERR live-blog headline style: "VAATA OTSE | Kas Eesti saab ka võõrsil Luksemburgist jagu?" [V].

Next step to get better real examples: screenshot Go3/TV3 app second-screen features and TV3 Play polls from a logged-in device, or ask the client for their existing interactive copy.

### 3.1 Lithuanian drafts (mine, need native review)

Informal *tu*. Club names in „…" and undeclined for foreign clubs.

1. **Poll:** Kas laimės šias rungtynes? Options: „Žalgiris" / „Rytas"
2. **Prediction:** Kas pelnys kitą įvartį? Options: Lietuva / Islandija / Niekas
3. **Prediction:** Ar rungtynės baigsis pratęsimu? Options: Taip / Ne
4. **Prediction:** Kiek tritaškių „Žalgiris" pataikys per trečiąjį kėlinį? Options: Iki 2 / 3–4 / 5 ir daugiau
5. **Prediction:** Ar Lietuva realizuos baudinį? Options: Taip, įmuš / Ne, vartininkas atrems
6. **Rating:** Kaip vertini teisėjų darbą šiame kėlinyje? Options: 1–5 žvaigždutės
7. **Quiz:** Kuri komanda per pirmąjį kėlinį atkovojo daugiau kamuolių? Options: „Žalgiris" / „Partizan" / Po lygiai

### 3.2 Latvian drafts (mine, need native review)

Informal *tu*. Note plural *vārti* throughout.

1. **Poll:** Kurš uzvarēs šajā spēlē? Options: Latvija / Kanāda
2. **Prediction:** Kurš gūs nākamos vārtus? Options: Latvija / Vācija / Neviens
3. **Prediction:** Vai spēle beigsies papildlaikā? Options: Jā / Nē
4. **Prediction:** Cik vārtu Latvija iemetīs vairākumā? Options: 0 / 1 / 2 un vairāk
5. **Prediction:** Vai Latvija realizēs 11 metru soda sitienu? Options: Jā, iesitīs / Nē, vārtsargs atvairīs
6. **Rating:** Kā tu vērtē vārtsarga sniegumu šajā periodā? Options: 1–5 zvaigznes
7. **Quiz:** Kurš pirmajā puslaikā izpildīja vairāk stūra sitienu? Options: Latvija / Armēnija / Vienādi

### 3.3 Estonian drafts (mine, need native review)

Informal *sina*. Names declined without quotes.

1. **Poll:** Kuidas mäng lõpeb? Options: Eesti võit / Viik / Läti võit
2. **Prediction:** Kes lööb järgmise värava? Options: Eesti / Bulgaaria / Keegi ei löö
3. **Prediction:** Mitu väravat lüüakse teisel poolajal? Options: 0 / 1–2 / 3 või rohkem
4. **Prediction:** Kas Eesti realiseerib penalti? Options: Jah / Ei, väravavaht tõrjub
5. **Prediction (basketball):** Kas mäng läheb lisaajale? Options: Jah / Ei
6. **Rating:** Kuidas hindad väravavahi esitust? Options: 1–5 tärni
7. **Quiz (basketball):** Kumb meeskond võttis avapoolajal rohkem lauapalle? Options: Kalev / Läti Ülikool / Võrdselt

---

## 4. Translationese tells natives flag

### Lithuanian
- Capitalized polite *Jūs* in casual UI; mixing *tu* and *jūs* in one screen.
- *Sekantis* for "next" (use *kitas*); *pilnai* for "fully"; *vardan* in the "for the sake of" sense (VLKK says not standard, use *dėl ko*) [V, [VLKK 6338](https://vlkk.lt/konsultacijos/6338-vardan)].
- Football *smūgis* used for basketball/hockey shots (should be *metimas*).
- *Baudos smūgis* for penalty (it's a free kick).
- English possessives everywhere (*jo komanda*, *savo žaidėjas*) where LT omits them.
- Passive "goal was scored by" (*įvartis buvo įmuštas X*) instead of active *X įmušė*.
- Unquoted club names, or declined foreign club names (*Barselonos* in a football context reads like the city).
- Slang mixed with formal copy: *golas*, *mačas*, *penalas* next to *rungtynės*.

### Latvian
- Singular *vārts / nākamo vārtu*.
- *Priekš* for "for".
- Keeping original spelling of player names (*Messi, Ronaldo*) instead of *Mesi, Ronaldu*.
- *Aizsegs* or *ofsaids* for offside.
- Bare *soda sitiens* for penalty.
- Overuse of *tikt* passives (*vārti tiks gūti*); active is natural (*kurš gūs vārtus*).
- *Šaiba*, *buliti* (Russian hockey slang) in polished copy.
- Calqued *jaudas spēle* for power play (use *vairākums*).

### Estonian
- *Karistuslöök* used for penalty.
- *Poolt* passives.
- *Arvuliselt ülekaalus* instead of *arvulises ülekaalus* [V, EKI].
- Wrong object case after negation (*ei löö väravat* is right; *ei löö värava* is wrong).
- Football *löök* used for hockey/basketball shots (should be *vise*).
- Unnecessary apostrophes on every foreign name (*Messi'st*).
- Futurity forced with *hakkab* (*hakkab võitma*).
- Teie-register in a fan app (*Vaadake*, *Teie arvamus*) when Go3 itself says *vaata*, *sinu*.
- õ/ö swaps and dropped ä/ü.

---

## 5. Recommendations for the generation pipeline

1. **Generate natively, don't translate.** Prompt per language with the glossary JSON injected and an instruction to use only glossary terms for listed concepts.
2. **Name forms come from a lookup, not the model.** Keep a per-language player/club form table (LT *Lionelis Messi*, LV *Lionels Mesi*, ET *Lionel Messi*) sourced from that country's press, plus a rule for club names (LT „…" undeclined foreign, LV "…" undeclined, ET declined no quotes).
3. **Deterministic validators** before publish: allowed character set per language; zero-diacritic flag; forbidden terms from each `avoid` list (e.g. LV `aizsegs`, ET `karistuslöök` in a penalty context, LT `sekantis`); LV regex for singular forms of *vārti*; question particle present for yes/no buffs (*Ar/Vai/Kas*); score format `\d+:\d+`; option length ≤ 25 chars.
4. **Native review** for anything marked [U] in this file and for every template before it goes live. The arXiv 1-in-20 figure is for open-weight models, but closed models still make the specific errors above.
5. **Reference sources to keep handy:** VLKK consultation bank and term bank (terminai.vlkk.lt; vlkk.lt is behind a Cloudflare challenge for scripts), EKI teatmik and Sõnaveeb, valodaskonsultacijas.lv, the LSPA/RSU English-Latvian sports dictionary PDF, and the native sports desks: 15min/LRT/basketnews.lt, LSM/sportacentrs/diena.lv, ERR/soccernet.ee.

## 6. What I couldn't verify

- VLKK's full grammaticalization rule text (site blocked automated fetches; only search snippets seen).
- Go3's in-app copy and any existing interactive/poll features (Cloudflare challenge).
- termini.gov.lv, IATE and EuroTermBank entries were not queried in this pass; the glossary leans on press usage plus the LSPA dictionary instead.
- Items marked `"verified": false` in the JSON: LT *raudonoji kortelė*, *keitimas*, *mažuma*, *kėlinys/ketvirtis* for basketball quarters, man-of-the-match phrasing; LV *ceturtdaļa*, *tukši vārti*; ET *veerandaeg*, *vähemus* in hockey, *pealevise*, and the phrase drafts.
