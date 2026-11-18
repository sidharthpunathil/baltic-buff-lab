"""Summarize a run: python -m bbl.analyze out/run-XXXX/results.json"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from statistics import mean

DIMS = ["grammar", "naturalness", "terminology", "faithfulness", "engagement"]


def score(j):
    return sum(j[d] for d in DIMS) / len(DIMS)


def penalty(j):
    w = {"minor": 1, "major": 5, "critical": 10}
    return sum(w[e["severity"]] for e in j["errors"])


def main(path: str) -> None:
    rows = json.load(open(path))
    g = defaultdict(list)
    for r in rows:
        g[(r["lang"], r["arm"])].append(r)
    print("| lang | arm | n | judge mean | naturalness | grammar | terminology | MQM penalty | approved | 2nd judge mean | 2nd approved | validator errors |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for (lang, arm), rs in sorted(g.items()):
        ok = [r for r in rs if r["judgement"]]
        xs = [r for r in ok if r.get("xjudgement")]
        if not ok:
            print(f"| {lang} | {arm} | 0 | failed | | | | | | | | |")
            continue
        verr = sum(sum(i.startswith("[error]") for i in r["issues"]) for r in ok)
        x_mean = f"{mean(score(r['xjudgement']) for r in xs):.2f}" if xs else "n/a"
        x_ok = f"{sum(r['xjudgement']['verdict'] == 'approve' for r in xs)}/{len(xs)}" if xs else "n/a"
        print(
            f"| {lang} | {arm} | {len(ok)} | {mean(score(r['judgement']) for r in ok):.2f} "
            f"| {mean(r['judgement']['naturalness'] for r in ok):.2f} | {mean(r['judgement']['grammar'] for r in ok):.2f} "
            f"| {mean(r['judgement']['terminology'] for r in ok):.2f} | {mean(penalty(r['judgement']) for r in ok):.1f} "
            f"| {sum(r['judgement']['verdict'] == 'approve' for r in ok)}/{len(ok)} | {x_mean} | {x_ok} ",
            end="",
        )
        print(f"| {verr} |")
    print()
    by_arm = defaultdict(Counter)
    for r in rows:
        if r["judgement"]:
            for e in r["judgement"]["errors"]:
                if e["severity"] != "minor":
                    by_arm[r["arm"]][e["category"]] += 1
    print("Major/critical judge errors by category:")
    for arm, c in sorted(by_arm.items()):
        print(f"  {arm}: {dict(c.most_common())}")
    codes = defaultdict(Counter)
    for r in rows:
        for i in r["issues"]:
            codes[r["arm"]][i.split(":")[0]] += 1
    print("Validator findings by arm:")
    for arm, c in sorted(codes.items()):
        print(f"  {arm}: {dict(c.most_common())}")
    reps = [len(r["trace"]) for r in rows if r["arm"] == "C.baltic" and r["trace"]]
    if reps:
        print(f"C rounds per buff: {Counter(reps)} (1 = accepted first draft)")
        first = [r["trace"][0]["judge"] for r in rows if r["arm"] == "C.baltic" and r["trace"]]
        print(f"C first-draft judge mean {mean(score(j) for j in first):.2f}, approved {sum(j['verdict']=='approve' for j in first)}/{len(first)}")
    errs = [f"{r['lang']} {r['arm']} {r['moment']}: {r['error']}" for r in rows if r["error"]]
    if errs:
        print("Failures:", *errs, sep="\n  ")


if __name__ == "__main__":
    main(sys.argv[1])
