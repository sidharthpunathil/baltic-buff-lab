"""python -m bbl.cli run samples/events/*.json --langs lt,lv,et --arms A,B,C"""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from rich.console import Console
from rich.table import Table

from . import report
from .config import OUT, settings
from .entities import resolve
from .inflect import forms_for
from .llm import USAGE
from .pipeline import run_event

console = Console()


def cmd_run(a) -> None:
    langs = a.langs.split(",")
    arms = a.arms.split(",")
    run_dir = OUT / time.strftime("run-%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    all_results = []
    for path in a.events:
        event = json.loads(Path(path).read_text())
        console.print(f"[bold]{event['home']} vs {event['away']}[/] ({event['sport']}) → {langs} arms={arms}")
        results = run_event(event, langs, arms, workers=a.workers)
        for r in results:
            all_results.append({"event": event, "result": r})
    (run_dir / "results.json").write_text(
        json.dumps([report.to_dict(x["event"], x["result"]) for x in all_results], ensure_ascii=False, indent=2)
    )
    html = report.render(all_results, settings, USAGE)
    (run_dir / "report.html").write_text(html)
    summarize(all_results)
    console.print(
        f"LLM calls={USAGE.calls} in={USAGE.input_tokens} out={USAGE.output_tokens} wall-sum={USAGE.seconds:.0f}s"
    )
    console.print(f"Report: {(run_dir / 'report.html').resolve()}")


def summarize(all_results) -> None:
    t = Table(title="Blind judge scores (mean over moments)")
    for c in ("lang", "arm", "n", "mean 1-5", "naturalness", "grammar", "terminology", "MQM penalty", "approved", "validator errors"):
        t.add_column(c)
    groups: dict[tuple, list] = {}
    for x in all_results:
        r = x["result"]
        groups.setdefault((r.lang, r.arm), []).append(r)
    for (lang, arm), rs in sorted(groups.items()):
        ok = [r for r in rs if r.judgement]
        if not ok:
            t.add_row(lang, arm, str(len(rs)), "error", "", "", "", "", "", "")
            continue
        m = lambda f: f"{statistics.mean(f(r) for r in ok):.2f}"
        t.add_row(
            lang, arm, str(len(ok)),
            m(lambda r: r.judgement.mean_score),
            m(lambda r: r.judgement.naturalness),
            m(lambda r: r.judgement.grammar),
            m(lambda r: r.judgement.terminology),
            m(lambda r: r.judgement.mqm_penalty),
            f"{sum(r.judgement.verdict == 'approve' for r in ok)}/{len(ok)}",
            str(sum(sum('[error]' in i for i in r.issues) for r in ok)),
        )
    console.print(t)


def cmd_entities(a) -> None:
    event = json.loads(Path(a.event).read_text())
    for e in event["entities"]:
        ent = resolve(e["name"], e["kind"], e.get("qid"))
        row = {l: ent.label(l) for l in ("lt", "lv", "et")}
        console.print(f"[bold]{e['name']}[/] {ent.qid} {row}")
        if a.forms:
            for l in a.langs.split(","):
                f = forms_for(ent, l)
                console.print(f"   {l}: {f.lemma} | " + "; ".join(f"{c.case}={c.short}" for c in f.forms))


def main() -> None:
    p = argparse.ArgumentParser(prog="bbl")
    sub = p.add_subparsers(required=True)
    r = sub.add_parser("run")
    r.add_argument("events", nargs="+")
    r.add_argument("--langs", default="lt,lv,et")
    r.add_argument("--arms", default="A,B,C")
    r.add_argument("--workers", type=int, default=6)
    r.set_defaults(fn=cmd_run)
    e = sub.add_parser("entities")
    e.add_argument("event")
    e.add_argument("--forms", action="store_true")
    e.add_argument("--langs", default="lt,lv,et")
    e.set_defaults(fn=cmd_entities)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
