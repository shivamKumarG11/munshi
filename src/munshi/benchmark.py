"""Benchmark the document reader on REAL scanned receipts (SROIE test split, expert labels).

v1: one vision call with a plain prompt.
v2: Munshi's reader (structured prompt, arithmetic checks, strong-model re-read on failure).
Scores: company, date and total exact-match (normalised).
"""

import json
import re
from datetime import datetime
from pathlib import Path

from munshi import llm, reader, tracing
from munshi.config import ROOT

BENCH = ROOT / "data/benchmark/sroie"

V1_PROMPT = 'Read this receipt. Reply JSON: {"company": "...", "date": "...", "total": "..."}'


def _norm_text(s) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def _norm_total(s) -> str:
    m = re.findall(r"\d+(?:\.\d+)?", str(s or "").replace(",", ""))
    return f"{float(m[-1]):.2f}" if m else ""


def _norm_date(s) -> str:
    s = str(s or "").strip()
    s = re.split(r"\s+\d{1,2}:\d{2}", s)[0].strip()   # drop a trailing time
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%Y-%m-%d", "%d.%m.%Y", "%d.%m.%y", "%d-%m-%y",
                "%d %b %Y", "%d %b %y", "%d %B %Y", "%d-%b-%Y", "%d-%b-%y", "%d/%b/%Y"):
        try:
            return datetime.strptime(s.title() if "%b" in fmt else s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s


def rescore(detail_file: Path) -> dict:
    """Re-score saved answers with the current normaliser (no model calls)."""
    d = json.loads(Path(detail_file).read_text(encoding="utf-8"))
    hits = {"company": 0, "date": 0, "total": 0}
    for r in d["rows"]:
        got, truth = r["got"], r["truth"]
        hits["company"] += _norm_text(got["company"]) == _norm_text(truth.get("company"))
        hits["date"] += _norm_date(got["date"]) == _norm_date(truth.get("date"))
        hits["total"] += _norm_total(got["total"]) == _norm_total(truth.get("total"))
    return {"version": d["version"], "n": len(d["rows"]), "accuracy": {k: round(v / len(d["rows"]), 3) for k, v in hits.items()}}


@tracing.span("WORKFLOW", name="reader_benchmark")
def run(n: int, version: str) -> dict:
    labels = json.loads((BENCH / "labels.json").read_text(encoding="utf-8"))
    keys = sorted(labels)[:n]
    hits = {"company": 0, "date": 0, "total": 0}
    rows = []
    for key in keys:
        img = BENCH / "images" / f"{key}.jpg"
        truth = labels[key]
        try:
            if version == "v1":
                got = llm.ask_json("vision", "You read receipts.", V1_PROMPT, images=[img])
                got = {"company": got.get("company"), "date": got.get("date"), "total": got.get("total")}
            else:
                r = reader.read(img, key, kind="receipt")
                got = {"company": r.document.party, "date": str(r.document.date or ""), "total": str(r.document.total)}
        except Exception as e:  # a failed read counts as wrong, and is visible in the trace
            got = {"company": None, "date": None, "total": None, "error": str(e)[:200]}
        ok = {
            "company": _norm_text(got["company"]) == _norm_text(truth.get("company")),
            "date": _norm_date(got["date"]) == _norm_date(truth.get("date")),
            "total": _norm_total(got["total"]) == _norm_total(truth.get("total")),
        }
        for k in hits:
            hits[k] += ok[k]
        rows.append({"key": key, "truth": truth, "got": got, "ok": ok})
    out = {"version": version, "n": len(keys), "dataset": "SROIE (ICDAR 2019) test split, real receipts, CC BY 4.0",
           "accuracy": {k: round(v / len(keys), 3) for k, v in hits.items()}, "llm_usage": llm.usage}
    dest = ROOT / "runs" / f"benchmark-{version}-{datetime.now():%Y%m%d-%H%M%S}.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps({**out, "rows": rows}, indent=1, default=str), encoding="utf-8")
    out["detail_file"] = str(dest)
    return out
