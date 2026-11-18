"""Wall-clock + token cost per stage for arm D (no evaluation panel), one moment per language."""
import json, time, statistics, sys
from bbl import llm, locale_pack, generate, reviewers, validators, inflect
from bbl.pipeline import entity_forms
PRICE = {"in": 4 / 1e6, "out": 20 / 1e6}  # claude-opus-5-5 $/token
rows = []
for path, lang in [("samples/events/basketball_zalgiris_real.json", "lt"), ("samples/events/hockey_latvia_canada.json", "lv"),
                   ("samples/events/football_estonia_italy.json", "et")]:
    ev = json.load(open(path)); m = ev["moments"][0]; pack = locale_pack.load(lang)
    forms = entity_forms(ev, lang, with_press=True); qids = [e["qid"] for e in ev["entities"]]
    u0 = (llm.USAGE.input_tokens, llm.USAGE.output_tokens, llm.USAGE.cache_write_tokens, llm.USAGE.cache_read_tokens)
    t0 = time.monotonic(); d = generate.arm_baltic_draft(ev, m, pack, forms); t1 = time.monotonic()
    iss = validators.check(d.buff, pack, ev["sport"], inflect.all_forms(forms)); t2 = time.monotonic()
    dec = reviewers.orchestrate(d.buff, ev, m, pack, forms, qids); t3 = time.monotonic()
    tin, tout = llm.USAGE.input_tokens - u0[0], llm.USAGE.output_tokens - u0[1]
    cw, cr = llm.USAGE.cache_write_tokens - u0[2], llm.USAGE.cache_read_tokens - u0[3]
    rows.append({"lang": lang, "generate_s": round(t1 - t0, 1), "validators_ms": round((t2 - t1) * 1000), "review_team_s": round(t3 - t2, 1),
                 "total_s": round(t3 - t0, 1), "tokens_in": tin, "tokens_out": tout, "cache_write": cw, "cache_read": cr,
                 "cost_usd": round(tin * PRICE["in"] + cw * PRICE["in"] * 1.25 + cr * PRICE["in"] * 0.05 + tout * PRICE["out"], 4),
                 "models": dec.ran, "blocking": len(dec.blocking)})
    print(rows[-1], flush=True)
json.dump(rows, open(sys.argv[1] if len(sys.argv) > 1 else "out/timing.json", "w"), indent=1)
for k in ("generate_s", "review_team_s", "total_s", "cost_usd"):
    print(k, "median", statistics.median(r[k] for r in rows))
