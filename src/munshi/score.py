"""Score a close run against the answer key. Pure code."""

import json
import re
from decimal import Decimal
from pathlib import Path

TRAPS = {
    "T01 duplicate upload detected": lambda f, e, a: any(all("cloudnest" in x.lower() for x in pair) for pair in f.get("duplicates", [])),
    "T02 missing bill flagged (not claimable)": lambda f, e, a: any(x["bank_txn_id"] == "B08" for x in a["missing_bills"]),
    "T03 one payment → three invoices": lambda f, e, a: len(_entry(e, "B16").get("document_ids", [])) == 3,
    "T04 partial payment, 38,500 open": lambda f, e, a: any(p and Decimal(p["open"]) == Decimal("38500") for p in f.get("partial_payments", [])),
    "T05 refund reduces Software": lambda f, e, a: _entry(e, "B15").get("account") == "Expenses:Software",
    "T06 cryptic payee → Software": lambda f, e, a: _entry(e, "B08").get("account") == "Expenses:Software",
    "T07 blurry receipt read (1,180)": lambda f, e, a: _amount(_entry(e, "B14")) == Decimal("-1180.00"),
    "T08 vendor arithmetic error flagged": lambda f, e, a: bool(f.get("vendor_errors")),
    "T09 un-invoiced work → invoice drafted": lambda f, e, a: any(i["client"].startswith("Zenith") for i in a["invoices"]),
    "T10 overdue invoice → reminder": lambda f, e, a: any(r["invoice"] == "KAV-2026-029" for r in a["reminders"]),
    "T11 books balance to the bank": lambda f, e, a: f.get("balanced") is True,
    "T12 personal expense not booked as business": lambda f, e, a: _entry(e, "B18").get("account") in ("Equity:Owner-Drawings", "Expenses:Uncategorised"),
}


def _entry(entries: list[dict], txn_id: str) -> dict:
    return next((x for x in entries if x["bank_txn_id"] == txn_id), {})


def _amount(entry: dict) -> Decimal | None:
    return Decimal(entry["amount"]) if entry else None


def score(run_dir: Path, key_path: Path) -> dict:
    key = json.loads(key_path.read_text(encoding="utf-8"))
    entries = json.loads((run_dir / "entries.json").read_text(encoding="utf-8"))
    facts = json.loads((run_dir / "facts.json").read_text(encoding="utf-8"))
    actions = json.loads((run_dir / "actions.json").read_text(encoding="utf-8"))
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    brief = (run_dir / "brief.md").read_text(encoding="utf-8")

    expected = {t["bank_txn_id"]: t for t in key["transactions"]}
    first_entry = {}
    counts: dict[str, int] = {}
    for e in entries:
        counts[e["bank_txn_id"]] = counts.get(e["bank_txn_id"], 0) + 1
        first_entry.setdefault(e["bank_txn_id"], e)
    correct = sum(1 for tid, t in expected.items() if first_entry.get(tid, {}).get("account") == t["account"])
    exact = sum(1 for tid, t in expected.items()
                if first_entry.get(tid, {}).get("account") == t["account"] and counts.get(tid) == 1
                and Decimal(first_entry[tid]["amount"]) == Decimal(t["amount"]))
    traps = {name: bool(check(facts, entries, actions)) for name, check in TRAPS.items()}
    exp_tax = key["expected_tax"]
    got_tax = facts.get("tax", {})
    tax_ok = (Decimal(got_tax.get("net_indirect_tax", "-1")) == Decimal(exp_tax["net_indirect_tax"]))

    # Brief faithfulness: every rupee figure in the brief must exist in the run's facts.
    known = {round(abs(float(v))) for v in _numbers(json.dumps(facts))}
    figures = [round(abs(float(x))) for x in re.findall(r"₹\s?([\d,]+(?:\.\d+)?)", brief.replace(",", "")) if x]
    unsupported_figures = [x for x in figures if x not in known and not any(abs(x - k) <= 1 for k in known)]

    # Does the brief state the TRUE profit (from the answer key)?
    true_income = sum((Decimal(t["amount"]) - Decimal(t["tax"]) for t in key["transactions"] if t["account"].startswith("Income")), Decimal("0"))
    true_exp = sum((-Decimal(t["amount"]) - Decimal(t["tax"]) for t in key["transactions"] if t["account"].startswith("Expenses")), Decimal("0"))
    true_profit = round(float(true_income - true_exp))
    brief_numbers = {round(float(x)) for x in re.findall(r"\d+(?:\.\d+)?", brief.replace(",", ""))}
    brief_profit_correct = any(abs(n - true_profit) <= 1 for n in brief_numbers)

    tokens = sum(u["prompt"] + u["completion"] for u in run["llm_usage"].values())
    calls = sum(u["calls"] for u in run["llm_usage"].values())
    return {
        "version": run["version"],
        "balanced": facts.get("balanced"),
        "bank_gap": facts.get("bank_gap"),
        "categorisation_accuracy": round(correct / len(expected), 3),
        "exact_entries": round(exact / len(expected), 3),
        "duplicate_posts": sum(n - 1 for n in counts.values() if n > 1),
        "traps_caught": sum(traps.values()), "traps_total": len(traps), "traps": traps,
        "net_indirect_tax_correct": tax_ok,
        "net_indirect_tax": got_tax.get("net_indirect_tax"), "expected_net_indirect_tax": exp_tax["net_indirect_tax"],
        "brief_unsupported_figures": unsupported_figures,
        "brief_states_true_profit": brief_profit_correct, "true_profit": true_profit,
        "llm_calls": calls, "llm_tokens": tokens, "seconds": run["seconds"], "models": list(run["llm_usage"].keys()),
    }


def _numbers(text: str) -> list[str]:
    return re.findall(r"-?\d+(?:\.\d+)?", text)
