# Buff Lab Live

A web app that runs the lab's real `bbl/` pipeline on a match moment and streams every step to the browser, so you can watch today's methods (A, B) and the new pipeline (C, D) write the same buff side by side.

```bash
cd baltic-buff-lab
app/run.sh            # builds the UI if needed, then serves UI + API at http://localhost:8765
```

For UI work, run `app/run.sh` in one terminal and `cd app/web && npm run dev` in another (http://localhost:5178, proxies `/api`).

## Two views

**Live comparison.** Pick a match, a moment (or write your own), a language and the methods, then press Run. Each column shows its buff, the English meaning, the automatic checks, the D reviewers and orchestrator, any repair rounds and the blind judge's verdict. Click any step to see the exact system prompt and user message that call received, the parsed output, tokens, time and cost.

**Pipeline inside.** The six stages from the deck, each opening onto the real data for the selected match and language: Wikidata labels, case tables before and after the press check, the style sheet, glossary and examples, the assembled prompt colour-coded by section next to today's prompts, a validator playground that runs the real checks as you type, and the five reviewers with their full prompts.

## How it hooks in

`app/server.py` changes nothing in `bbl/`. It wraps a few module functions (`llm.structured`, the generator, `validators.check`, `reviewers.run_specialist`, `reviewers.orchestrate`, `judge.judge`) so each call also emits an event, and streams those events as NDJSON from `POST /api/run`. A context variable tags every event with its method and repair round; reviewer threads inherit it through a context-copying thread pool.

Live defaults differ from batch runs in two ways: the native-ear reviewer uses Claude instead of the Gemini chain, and the second-vendor judge is off (Gemini overloads made single reviews take minutes). Set `BBL_NATIVE_EAR_MODEL` or `BBL_LIVE_XJUDGE_MODEL` to change that.

Costs use $4 / $20 per million tokens for Opus 5.5 and $2 / $10 for Sonnet 5.5, with cache writes at 1.25x and cache reads at 0.05x input. A typical A + B + D run with the judge costs about 25 cents.
