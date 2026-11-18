# Snippets (verified 2026-11-17)

| File | What | Needs |
|---|---|---|
| `wikidata_wbgetentities.py` | lt/lv/et labels, aliases, Wikipedia titles for players/clubs/competitions via Action API | stdlib |
| `wikidata_labels.py` | Same via SPARQL (WDQS). WDQS returned HTTP 429 "1 req/min" during an outage on test day | stdlib |
| `wikidata_output_2026-11-17.jsonl` | Output of the Action API script on test day | - |
| `latvian_morpho_api.py` | Inflect LV names/phrases + OOV check via morpho-api.tezaurs.lv | stdlib |
| `estonian_vabamorf.py` | ET case synthesis, built-in speller, morph tagging via EstNLTK/Vabamorf | `estnltk==1.7.5`, Python 3.12 |
| `hunspell_check.py` | lt_LT / lv_LV / et_EE hunspell via spylls + dictionaries bundled in phunspell | `spylls phunspell` |
| `tartunlp_mt.py` | TartuNLP public MT API (en->et/lv/lt) | stdlib |
| `sports_rss.py` | Native sports headline feeds (LRT, LSM, Sportacentrs, ERR Sport) | stdlib |
| `euroeval_ranks.py` | Parse EuroEval leaderboard CSVs: `python3 euroeval_ranks.py lithuanian "claude|gemma" 30` (run in a dir holding `<lang>_all.csv` from github.com/EuroEval/leaderboards/tree/main/leaderboards) | stdlib |
