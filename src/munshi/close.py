"""The month close: the coordinator that runs every step and only stops when the books balance.

v1 = the naive first attempt (kept for the before/after): strong model everywhere, no arithmetic
     checks, bills entered as read, no bank reconciliation, brief written freely by the LLM.
v2 = Munshi: cheap-first reading with code checks, rules + Crustdata + owner questions, bills entered
     then RECONCILED against the bank (gap hunt + repair), tax and brief computed from the ledger.
"""

import csv
import json
import re
import subprocess
import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Callable

from rapidfuzz import fuzz

from munshi import bank as bankmod
from munshi import categoriser, ledger, llm, matcher, reader, tracing
from munshi.config import ROOT
from munshi.matcher import IssuedInvoice
from munshi.models import BankTxn, Document, Entry

Progress = Callable[[str, str, dict | None], None]


def _noop(step: str, message: str, data: dict | None = None) -> None:
    print(f"[{step}] {message}")


# --------------------------------------------------------------------------- inputs

def load_month(month_dir: Path) -> dict:
    biz = json.loads((month_dir / "business.json").read_text(encoding="utf-8"))
    issued = []
    if (month_dir / "invoices_issued.csv").exists():
        with open(month_dir / "invoices_issued.csv", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                issued.append(IssuedInvoice(number=r["number"], client=r["client"], date=date.fromisoformat(r["date"]),
                                            subtotal=Decimal(r["subtotal"]), tax=Decimal(r["tax"]), total=Decimal(r["total"])))
    timesheet = []
    if (month_dir / "timesheet.csv").exists():
        with open(month_dir / "timesheet.csv", encoding="utf-8") as f:
            timesheet = list(csv.DictReader(f))
    answers_path = month_dir / "owner_answers.json"
    return {
        "business": biz,
        "bank": load_bank(month_dir),
        "issued": issued,
        "timesheet": timesheet,
        "owner_answers": json.loads(answers_path.read_text(encoding="utf-8")) if answers_path.exists() else {},
        "doc_files": sorted(p for p in (month_dir / "documents").iterdir()
                            if p.suffix.lower() in {".pdf", ".png", ".jpg", ".jpeg"} and ".page" not in p.name),
    }


def load_bank(month_dir: Path):
    """The statement plus any addendum files that arrived later (bank_statement*.csv), checked for continuity."""
    rows = []
    for path in sorted(month_dir.glob("bank_statement*.csv"), key=lambda p: (p.stem != "bank_statement", p.name)):
        part = bankmod.parse(path)
        if rows and part and rows[-1].balance is not None and part[0].balance is not None \
                and rows[-1].balance + part[0].amount != part[0].balance:
            raise ValueError(f"{path.name} doesn't continue from the previous statement balance")
        seen = {r.id for r in rows}
        rows += [r for r in part if r.id not in seen]
    return rows


def _slug(name: str) -> str:
    return re.sub(r"\W+", "-", name.lower()).strip("-")


# --------------------------------------------------------------------------- memory (incremental closes)

MEMORY = ROOT / "state" / "memory"


def _mem_load(biz: dict) -> dict:
    path = MEMORY / f"{_slug(biz['name'])}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"categorised": {}}


def _mem_save(biz: dict, mem: dict) -> None:
    MEMORY.mkdir(parents=True, exist_ok=True)
    (MEMORY / f"{_slug(biz['name'])}.json").write_text(json.dumps(mem, indent=1, default=str), encoding="utf-8")


def _categorise_remembered(mem, txn, doc, doc_hash, vendor_error, entries, answers, non_claimable):
    """Re-use an earlier decision for the same bank line + same evidence; only new things go to the model."""
    key = f"{txn.id}|{txn.description}|{txn.amount}|{doc_hash or ''}|{vendor_error}"
    hit = mem["categorised"].get(key)
    if hit:
        return Entry(**{**hit["entry"], "date": txn.date}), hit.get("question"), True
    e, q = categoriser.categorise(txn, doc, vendor_error, entries, answers, non_claimable)
    mem["categorised"][key] = {"entry": e.model_dump(mode="json"), "question": q.model_dump() if q else None}
    return e, (q.model_dump() if q else None), False


# --------------------------------------------------------------------------- bill entry

def _bank_line_for_bill(doc: Document, bank: list[BankTxn]) -> BankTxn | None:
    """Where a bookkeeper would record this bill: the debit from the same party (amount may differ)."""
    best, best_score = None, 0
    for t in (t for t in bank if t.amount < 0):
        score = fuzz.partial_ratio(re.sub(r"\W", " ", doc.party.upper()), t.description.upper())
        if doc.number and re.sub(r"\W", "", doc.number.upper()) in re.sub(r"\W", "", t.description.upper()):
            score += 40
        if abs(-t.amount - doc.total) <= Decimal("0.01"):
            score += 20
        if score > best_score:
            best, best_score = t, score
    return best if best_score >= 60 else None


# --------------------------------------------------------------------------- v2

@tracing.span("WORKFLOW", name="munshi_close_v2")
def close_v2(month_dir: Path, out_dir: Path, progress: Progress = _noop, live_actions: bool = False,
             with_peers: bool = True, previous: dict | None = None) -> dict:
    t0 = time.time()
    m = load_month(month_dir)
    biz, bank = m["business"], m["bank"]
    opening, closing = bankmod.opening_balance(bank), bankmod.closing_balance(bank)
    period_start, period_end = bank[0].date.replace(day=1), _month_end(bank[0].date)
    non_claimable = set(biz.get("non_claimable_tax_accounts", []))
    if biz.get("input_credit_allowed") is False:
        non_claimable.add("*")
    mem = _mem_load(biz)
    progress("plan", f"{len(bank)} bank lines, {len(m['doc_files'])} documents, {len(m['issued'])} issued invoices",
             {"opening": str(opening), "closing": str(closing)})

    peers = None
    if with_peers:
        from munshi import peers as peersmod
        progress("research", f"Finding real peers in industries {biz['peer_sics']} (SEC EDGAR)")
        peers = peersmod.research(biz["peer_sics"])
        progress("research", f"{len(peers['peers'])} peers; median operating margin "
                             f"{peers['median_operating_margin']:.1%}", {"peers": [p["name"] for p in peers["peers"]]})

    # 1. Read documents (cheap first, code checks, strong re-read on failure)
    docs, hashes, reads = [], {}, {}
    for i, path in enumerate(m["doc_files"], start=1):
        r = reader.read(path, path.name, kind="receipt" if path.suffix.lower() != ".pdf" else "bill")
        docs.append(r.document); hashes[r.document.id] = r.content_hash; reads[r.document.id] = r
        flag = " ⚠ vendor error" if r.vendor_error else (" (re-read with strong model)" if r.model_role == "strong" else "")
        flag += " (remembered)" if getattr(r, "remembered", False) else ""
        progress("read", f"{path.name}: {r.document.party} ₹{r.document.total}{flag}")
    correct_totals = {d.id: (d.subtotal + d.tax) if reads[d.id].vendor_error and d.subtotal is not None else d.total
                      for d in docs}

    # 2. Match: duplicates, client payments, bills
    mr = matcher.match(bank, docs, hashes, correct_totals, m["issued"])
    for dup, orig in mr.duplicates:
        progress("match", f"{dup} looks like a duplicate of {orig} (identical upload)")

    # 3. Enter bills as they arrive (a bookkeeper doesn't know yet which uploads are duplicates)
    entries: list[Entry] = []
    questions = []
    by_doc = {d.id: d for d in docs}
    for doc in docs:
        txn = _bank_line_for_bill(doc, bank)
        if txn is None:
            continue
        e, _, _ = _categorise_remembered(mem, txn, doc, hashes[doc.id], reads[doc.id].vendor_error, entries, {},
                                         non_claimable)
        e = e.model_copy(update={"amount": -doc.total})  # recorded at the bill's printed total
        entries.append(e)
    progress("post", f"Entered {len(entries)} bills")

    # 4. Everything else from the bank: client receipts, rules, unknown payees
    billed = {e.bank_txn_id for e in entries}
    for txn in bank:
        if txn.id in billed:
            continue
        if txn.id in mr.payments:
            p = mr.payments[txn.id]
            entries.append(categoriser.income_entry(txn, p.invoices, p.tax, p.partial))
            progress("post", f"{txn.id} client payment → {', '.join(p.invoices)}" + (" (partial)" if p.partial else ""))
            continue
        e, q, remembered = _categorise_remembered(mem, txn, None, None, False, entries, m["owner_answers"], non_claimable)
        e = _sales_tax(e, biz)
        entries.append(e)
        if q:
            questions.append(q)
        progress("post", f"{txn.id} {txn.description[:40]} → {e.account}"
                 + (" (remembered)" if remembered else f" ({e.decided_by})"))

    # 5. Verify against the bank; hunt and repair gaps until the books balance
    def verify(es):
        text = ledger.render(es, opening, period_start, closing, period_end)
        return text, ledger.check(text, closing)

    text, result = verify(entries)
    hunts = []
    attempt = 0
    while (not result.ok or result.bank_gap != 0) and attempt < 3:
        attempt += 1
        progress("verify", f"✗ Books don't balance: ledger vs bank gap ₹{result.bank_gap}", {"gap": str(result.bank_gap)})
        gaps = ledger.find_gaps(entries, bank)
        for g in gaps:
            why = _explain_gap(g, entries, mr, reads, by_doc)
            hunts.append({**g.model_dump(mode="json"), "explanation": why})
            progress("gap_hunt", f"{g.kind} on {g.bank_txn_id}: {why}", {"effect": str(g.effect)})
        entries = ledger.repair(entries, gaps, bank)
        for g in (g for g in gaps if g.kind == "missing_post"):
            txn = next(t for t in bank if t.id == g.bank_txn_id)
            e, q, _ = _categorise_remembered(mem, txn, None, None, False, entries, m["owner_answers"], non_claimable)
            entries.append(_sales_tax(e, biz))
        text, result = verify(entries)
    progress("verify", "✅ Books balance to the bank: ₹0 difference" if result.ok and result.bank_gap == 0
             else f"✗ Still off by ₹{result.bank_gap}; escalating to a human", {"gap": str(result.bank_gap)})

    # 6. Tax, actions, brief: all computed from the ledger
    tax = _tax(entries, biz)
    actions = _actions(m, mr, entries, bank, biz, live_actions, progress)
    facts = _facts(entries, opening, closing, result, tax, actions, questions, mr, reads, peers, hunts)
    facts["actions"] = actions
    brief = _brief_v2(biz, period_end, facts)
    progress("brief", "Morning brief ready")

    _mem_save(biz, mem)
    if previous:
        facts["changes"] = diff(previous, entries, facts, actions)
        for c in facts["changes"]:
            progress("update", c)
    out = _save(out_dir, "v2", text, entries, facts, brief, actions, m, period_end, t0)
    _commit_books(biz, period_end, text, facts)
    return out


def _explain_gap(g, entries, mr, reads, by_doc) -> str:
    if g.kind == "duplicate_post":
        docs_here = [d for e in entries if e.bank_txn_id == g.bank_txn_id for d in e.document_ids]
        dupe = next(((d, o) for d, o in mr.duplicates if d in docs_here or o in docs_here), None)
        if dupe:
            src = lambda i: reads[i].document.source.rsplit("/", 1)[-1]
            return f"{src(dupe[0])} is the same file as {src(dupe[1])}, uploaded twice; keep one"
        return "the same payment was entered twice; keep one"
    if g.kind == "amount_mismatch":
        doc_id = next((d for e in entries if e.bank_txn_id == g.bank_txn_id for d in e.document_ids), None)
        if doc_id and reads[doc_id].vendor_error:
            d = by_doc[doc_id]
            return (f"vendor's bill {d.number} prints total ₹{d.total}, but its lines add to ₹{d.subtotal + d.tax}; "
                    f"the bank paid the correct amount, so book the bank figure and flag the vendor")
        return "recorded amount differs from the bank; use the bank figure"
    if g.kind == "missing_post":
        return "bank line never recorded; categorising it now"
    return "entry points at a bank line that doesn't exist; removing it"


def _sales_tax(e: Entry, biz: dict) -> Entry:
    """Shop/café sales settle tax-inclusive: carve the output tax out of the receipt at the configured rate."""
    if e.account == "Income:Sales" and e.amount > 0 and biz.get("sales_tax_inclusive") and not e.tax:
        rate = Decimal(biz.get("gst_rate", "0"))
        return e.model_copy(update={"tax": (e.amount * rate / (1 + rate)).quantize(Decimal("0.01"))})
    return e


def diff(previous: dict, entries: list[Entry], facts: dict, actions: dict) -> list[str]:
    """Plain-language list of what changed since the previous close of this month."""
    changes = []
    prev_entries = {e["bank_txn_id"]: e for e in previous["entries"]}
    for e in entries:
        old = prev_entries.get(e.bank_txn_id)
        if old is None:
            changes.append(f"New bank line {e.bank_txn_id} ({e.payee[:34]}, {_inr(e.amount)}) booked as "
                           f"{e.account.split(':')[-1]}")
        elif old["document_ids"] != e.document_ids and e.document_ids:
            changes.append(f"{e.bank_txn_id} now has its bill ({', '.join(e.document_ids)})")
        elif old["account"] != e.account:
            changes.append(f"{e.bank_txn_id} moved from {old['account'].split(':')[-1]} to {e.account.split(':')[-1]}")
    pa, pf = previous["actions"], previous["facts"]
    for r in pa.get("reminders", []):
        if r["invoice"] not in {x["invoice"] for x in actions["reminders"]}:
            changes.append(f"{r['client']} paid {r['invoice']}: reminder no longer needed")
    for mb in pa.get("missing_bills", []):
        if mb["bank_txn_id"] not in {x["bank_txn_id"] for x in actions["missing_bills"]}:
            changes.append(f"Missing bill for {mb['bank_txn_id']} resolved")
    for key, label in [("set_aside", "Tax to set aside"), ("profit", "Profit"), ("input_tax_claimable", "Claimable tax")]:
        a, b = Decimal(pf["tax"][key]), Decimal(facts["tax"][key])
        if a != b:
            changes.append(f"{label}: {_inr(a)} → {_inr(b)}")
    if pf.get("balanced") != facts.get("balanced"):
        changes.append("Books now balance to the bank" if facts["balanced"] else "Books no longer balance: needs a look")
    return changes or ["Nothing changed in the books"]


def _tax(entries: list[Entry], biz: dict) -> dict:
    output = sum((e.tax for e in entries if e.account in ("Income:Services", "Income:Sales")), Decimal("0"))
    input_ = sum((e.tax for e in entries if e.amount < 0), Decimal("0"))
    income = sum((-(e.amount - e.tax) * -1 for e in entries if e.account.startswith("Income")), Decimal("0"))
    expenses = sum((-(e.amount) - e.tax for e in entries if e.account.startswith("Expenses")), Decimal("0"))
    profit = income - expenses
    rate = Decimal(biz.get("income_tax_provision_rate", "0.25"))
    provision = max(profit * rate, Decimal("0")).quantize(Decimal("0.01"))
    net = output - input_
    return {"assumptions": {"gst_rate": biz.get("gst_rate"), "income_tax_provision_rate": str(rate),
                            "non_claimable": biz.get("non_claimable_tax_accounts", [])},
            "output_tax_collected": str(output), "input_tax_claimable": str(input_), "net_indirect_tax": str(net),
            "revenue_ex_tax": str(income), "expenses_ex_tax": str(expenses), "profit": str(profit),
            "income_tax_provision": str(provision), "set_aside": str((net + provision).quantize(Decimal("0.01")))}


def _actions(m, mr, entries, bank, biz, live, progress) -> dict:
    period_end = _month_end(bank[0].date)
    rate = Decimal(biz.get("hourly_rate", "2000"))
    gst = Decimal(biz.get("gst_rate", "0.18"))
    drafts = []
    for row in m["timesheet"]:
        if "not invoiced" in row["billing_status"].lower():
            sub = rate * Decimal(row["hours"])
            total = (sub * (1 + gst)).quantize(Decimal("0.01"))
            draft = {"type": "invoice", "client": row["client"], "project": row["project"], "hours": row["hours"],
                     "subtotal": str(sub), "tax": str(total - sub), "total": str(total),
                     "number": f"KAV-{period_end:%Y}-DRAFT-{len(drafts) + 1:02d}"}
            if live:
                from munshi.integrations import dodo
                email = biz.get("client_emails", {}).get(row["client"], "accounts@example.com")
                draft["dodo"] = dodo.payment_link(draft["number"], f"{row['project']} ({row['hours']} h)", total,
                                                  row["client"], email)
            drafts.append(draft)
            progress("actions", f"Un-invoiced work: {row['client']} {row['hours']} h → draft invoice ₹{total}"
                                + (" with Dodo payment link" if live else ""))
    terms = int(biz.get("payment_terms_days", 15))
    reminders = []
    for inv in mr.open_invoices:
        due = date.fromisoformat(inv["date"]) + timedelta(days=terms)
        overdue = (period_end - due).days
        if overdue > 0:
            reminders.append({"type": "reminder", "invoice": inv["number"], "client": inv["client"],
                              "open": inv["open"], "days_overdue": overdue,
                              "tone": "firm" if overdue > 30 else "polite"})
            progress("actions", f"{inv['number']} {inv['client']}: ₹{inv['open']} open, {overdue} days overdue → reminder")
    missing = [{"type": "missing_bill", "bank_txn_id": e.bank_txn_id, "payee": e.payee, "amount": str(-e.amount)}
               for e in entries if e.amount < 0 and not e.document_ids and e.account.startswith("Expenses")
               and not e.decided_by.startswith("rule:") and e.decided_by != "owner"]
    for x in missing:
        progress("actions", f"{x['bank_txn_id']} {x['payee']}: no bill, so not claimable yet → request drafted")
    return {"invoices": drafts, "reminders": reminders, "missing_bills": missing}


def _facts(entries, opening, closing, result, tax, actions, questions, mr, reads, peers, hunts) -> dict:
    revenue, profit = Decimal(tax["revenue_ex_tax"]), Decimal(tax["profit"])
    facts = {
        "balanced": bool(result.ok and result.bank_gap == 0), "bank_gap": str(result.bank_gap),
        "opening_balance": str(opening), "closing_balance": str(closing),
        "tax": tax, "questions": questions, "gap_hunt": hunts,
        "duplicates": [[reads[d].document.source.rsplit("/", 1)[-1], reads[o].document.source.rsplit("/", 1)[-1]] for d, o in mr.duplicates], "partial_payments": [p.partial for p in mr.payments.values() if p.partial],
        "vendor_errors": [{"doc": r.document.source.rsplit("/", 1)[-1], "party": r.document.party, "printed_total": str(r.document.total), "issues": r.issues}
                          for d, r in reads.items() if r.vendor_error],
        "open_invoices": mr.open_invoices,
        "operating_margin": round(float(profit / revenue), 4) if revenue else None,
        "evidence_coverage": round(sum(1 for e in entries if e.document_ids or e.decided_by.startswith(("rule", "owner", "match"))
                                       or "crustdata" in e.decided_by) / max(len(entries), 1), 4),
        "unsupported_posts": sum(1 for e in entries if not e.document_ids and e.decided_by.startswith("llm:")
                                 and e.account != categoriser.UNSURE and e.amount < 0 and e.confidence < 0.6),
    }
    if peers:
        facts["peers"] = {"median_operating_margin": peers["median_operating_margin"],
                          "median_effective_tax_rate": peers["median_effective_tax_rate"],
                          "companies": [{k: p.get(k) for k in ("name", "cik", "revenue_usd", "operating_margin",
                                                               "effective_tax_rate", "sic")} for p in peers["peers"]],
                          "source": peers["source"]}
    return facts


def _inr(x) -> str:
    x = Decimal(str(x))
    sign = "-" if x < 0 else ""
    x = abs(x).quantize(Decimal("1"))
    s = str(x)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = f"{head},{tail}"
    return f"{sign}₹{s}"


def _brief_v2(biz: dict, period_end: date, f: dict) -> str:
    t = f["tax"]
    lines = [f"# {biz['name']}: {period_end:%B %Y}", ""]
    lines.append(("**Closed ✅**: books balance to the bank (₹0 difference)" if f["balanced"]
                  else f"**Not closed ✗**: books are off by {_inr(f['bank_gap'])}; needs a human"))
    if f["gap_hunt"]:
        lines.append(f"- 🔎 **Fixed during the close:** " + "; ".join(h["explanation"] for h in f["gap_hunt"]))
    lines += ["",
              f"- **Profit:** {_inr(t['profit'])} (revenue {_inr(t['revenue_ex_tax'])}, expenses {_inr(t['expenses_ex_tax'])}, excl. tax)",
              f"- **Tax to set aside:** ≈ {_inr(t['set_aside'])}: estimate from your settings "
              f"(net GST {_inr(t['net_indirect_tax'])} = collected {_inr(t['output_tax_collected'])} − claimable "
              f"{_inr(t['input_tax_claimable'])}; income-tax provision {Decimal(t['assumptions']['income_tax_provision_rate']):.0%} "
              f"of profit = {_inr(t['income_tax_provision'])})"]
    if f.get("peers") and f["peers"]["median_operating_margin"] is not None and f["operating_margin"] is not None:
        names = ", ".join(c["name"] for c in f["peers"]["companies"][:4])
        lines.append(f"- **Compared with real peers:** your operating margin this month {f['operating_margin']:.0%} vs "
                     f"{f['peers']['median_operating_margin']:.0%} median for {len(f['peers']['companies'])} listed agencies/"
                     f"consultancies ({names}…; SEC filings)")
    if f["vendor_errors"]:
        lines.append(f"- ⚠ **Vendor bill error:** " + "; ".join(f"{v['doc']}: {v['issues'][0]}" for v in f["vendor_errors"]))
    if f["partial_payments"]:
        lines.append("- 💸 **Part-paid:** " + "; ".join(f"{p['invoice']} paid {_inr(p['paid'])}, {_inr(p['open'])} still open"
                                                       for p in f["partial_payments"]))
    a = f.get("actions", {})
    for inv in a.get("invoices", []):
        link = " (payment link ready)" if inv.get("dodo") else ""
        lines.append(f"- 🧾 **Never invoiced:** {inv['client']}, {inv['project']} ({inv['hours']} h): {_inr(inv['total'])} invoice drafted{link}")
    for r in a.get("reminders", []):
        lines.append(f"- ⏰ **Overdue:** {r['invoice']} {r['client']} {_inr(r['open'])}, {r['days_overdue']} days, {r['tone']} reminder drafted")
    for mb in a.get("missing_bills", []):
        lines.append(f"- 📎 **Missing bill:** {mb['payee']} {_inr(mb['amount'])}: not claimable until the bill arrives; request drafted")
    for q in f.get("questions", []):
        lines.append(f"- ❓ **Question for you:** {q['text']}")
    lines.append("")
    lines.append("*Every number links to a ledger line and its source document.*")
    return "\n".join(lines) + "\n"


def _save(out_dir, version, ledger_text, entries, facts, brief, actions, m, period_end, t0) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ledger.beancount").write_text(ledger_text, encoding="utf-8")
    (out_dir / "entries.json").write_text(json.dumps([e.model_dump(mode="json") for e in entries], indent=1), encoding="utf-8")
    (out_dir / "facts.json").write_text(json.dumps(facts, indent=1, default=str), encoding="utf-8")
    (out_dir / "brief.md").write_text(brief, encoding="utf-8")
    (out_dir / "actions.json").write_text(json.dumps(actions, indent=1, default=str), encoding="utf-8")
    _actuals_csv(out_dir / "monthly_actuals.csv", entries, period_end, m["business"]["name"])
    run = {"version": version, "seconds": round(time.time() - t0, 1), "llm_usage": llm.usage,
           "finished_at": datetime.now().isoformat(timespec="seconds"), "out_dir": str(out_dir)}
    (out_dir / "run.json").write_text(json.dumps(run, indent=1), encoding="utf-8")
    return {**run, "facts": facts, "brief": brief, "actions": actions}


def _actuals_csv(path: Path, entries: list[Entry], period_end: date, business: str) -> None:
    """Monthly actuals by account (ex-tax), one row per line item, ready for any planning tool or spreadsheet."""
    totals: dict[str, Decimal] = {}
    for e in entries:
        if e.account.startswith(("Income", "Expenses")):
            totals[e.account] = totals.get(e.account, Decimal("0")) + (e.amount - (e.tax if e.amount > 0 else -e.tax))
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["company", "month", "account", "type", "amount_inr"])
        for acct, amt in sorted(totals.items()):
            w.writerow([business, f"{period_end:%Y-%m}", acct.split(":", 1)[1],
                        "revenue" if acct.startswith("Income") else "expense", f"{abs(amt):.2f}"])


def _commit_books(biz: dict, period_end: date, ledger_text: str, facts: dict) -> None:
    """Books as code: the closed month is committed to the business's own ledger repository."""
    repo = ROOT / "ledgers" / re.sub(r"\W+", "-", biz["name"].lower()).strip("-")
    repo.mkdir(parents=True, exist_ok=True)
    if not (repo / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / f"{period_end:%Y-%m}.beancount").write_text(ledger_text, encoding="utf-8")
    (repo / f"{period_end:%Y-%m}.facts.json").write_text(json.dumps(facts, indent=1, default=str), encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    msg = f"Close {period_end:%Y-%m}: " + ("balanced" if facts["balanced"] else f"OFF by {facts['bank_gap']}")
    subprocess.run(["git", "-c", "user.name=Munshi", "-c", "user.email=munshi@localhost", "commit", "-qm", msg,
                    "--allow-empty"], cwd=repo, check=False)


def _month_end(d: date) -> date:
    nxt = (d.replace(day=28) + timedelta(days=4)).replace(day=1)
    return nxt - timedelta(days=1)


# --------------------------------------------------------------------------- v1 (naive, for comparison)

V1_DOC = """You are a bookkeeper. Extract this document and choose where it goes in the books.
Reply JSON: {"party": "...", "number": "...", "date": "YYYY-MM-DD", "total": number, "tax": number,
"account": one of [%s], "bank_txn_id": the id of the bank line that paid it}"""

V1_TXN = """You are a bookkeeper. Categorise this bank transaction.
Reply JSON: {"account": one of [%s], "reason": "..."}"""

V1_BRIEF = """Write a short month-end brief for the business owner (profit, tax to set aside, anything to
watch). Use markdown bullets."""


@tracing.span("WORKFLOW", name="munshi_close_v1")
def close_v1(month_dir: Path, out_dir: Path, progress: Progress = _noop) -> dict:
    t0 = time.time()
    m = load_month(month_dir)
    bank = m["bank"]
    opening, closing = bankmod.opening_balance(bank), bankmod.closing_balance(bank)
    period_start, period_end = bank[0].date.replace(day=1), _month_end(bank[0].date)
    accounts = ", ".join(categoriser.ACCOUNTS)
    debits = "\n".join(f"{t.id} {t.date} {t.description} {t.amount}" for t in bank if t.amount < 0)
    entries: list[Entry] = []
    by_id = {t.id: t for t in bank}
    for i, path in enumerate(m["doc_files"], start=1):
        prompt = f"Bank debits this month:\n{debits}\n\nRead the attached document."
        if path.suffix.lower() == ".pdf":
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                text = "\n".join(p.extract_text() or "" for p in pdf.pages)
            r = llm.ask_json("strong", V1_DOC % accounts, prompt + "\n\nDocument text:\n" + text)
        else:
            r = llm.ask_json("strong", V1_DOC % accounts, prompt, images=[path])
        txn = by_id.get(str(r.get("bank_txn_id")))
        if not txn:
            continue
        total = Decimal(str(r.get("total") or 0))
        entries.append(Entry(bank_txn_id=txn.id, date=txn.date, payee=txn.description, narration=r.get("party", ""),
                             account=categoriser._valid(r.get("account", "")), amount=-total,
                             tax=Decimal(str(r.get("tax") or 0)), document_ids=[f"D{i:02d}"],
                             decided_by=f"llm:{llm.model_for('strong')}"))
        progress("read", f"{path.name} → {r.get('account')} ₹{total} on {txn.id}")
    done = {e.bank_txn_id for e in entries}
    for txn in (t for t in bank if t.id not in done):
        r = llm.ask_json("strong", V1_TXN % accounts, f"{txn.date} {txn.description} {txn.amount}")
        account = categoriser._valid(r.get("account", ""))
        tax = (txn.amount * Decimal(18) / Decimal(118)).quantize(Decimal("0.01")) if account == "Income:Services" else Decimal("0")
        entries.append(Entry(bank_txn_id=txn.id, date=txn.date, payee=txn.description, narration=r.get("reason", ""),
                             account=account, amount=txn.amount, tax=tax, decided_by=f"llm:{llm.model_for('strong')}"))
        progress("post", f"{txn.id} {txn.description[:40]} → {account}")
    text = ledger.render(entries, opening, period_start, closing, period_end)
    result = ledger.check(text, closing)
    tax = _tax(entries, m["business"])
    summary = json.dumps([{"account": e.account, "amount": str(e.amount), "tax": str(e.tax)} for e in entries])
    brief = llm.ask_json("strong", V1_BRIEF + ' Reply JSON: {"brief": "markdown"}', summary).get("brief", "")
    progress("brief", "v1 brief written by the LLM (no reconciliation)")
    facts = {"balanced": bool(result.ok and result.bank_gap == 0), "bank_gap": str(result.bank_gap), "tax": tax,
             "questions": [], "gap_hunt": [], "duplicates": [], "partial_payments": [], "vendor_errors": [],
             "open_invoices": [], "opening_balance": str(opening), "closing_balance": str(closing)}
    actions = {"invoices": [], "reminders": [], "missing_bills": []}
    return _save(out_dir, "v1", text, entries, facts, brief, actions, m, period_end, t0)
