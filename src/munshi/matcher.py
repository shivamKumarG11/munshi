"""Link bank lines to documents and issued invoices. Deterministic; no LLM.

- Duplicate uploads: identical files, or same party + number + total.
- Bills ↔ debits: amount equals the bill's correct total, date window, party similarity or reference.
- Client receipts ↔ issued invoices: invoice numbers in the narration, else an exact subset of the
  client's open invoices, else a partial payment against the oldest open invoice.
"""

import itertools
import re
from datetime import date, timedelta
from decimal import Decimal

from pydantic import BaseModel
from rapidfuzz import fuzz

from munshi import tracing
from munshi.models import BankTxn, Document

TOL = Decimal("0.01")


class IssuedInvoice(BaseModel):
    number: str
    client: str
    date: date
    subtotal: Decimal
    tax: Decimal
    total: Decimal


class InvoicePayment(BaseModel):
    bank_txn_id: str
    invoices: list[str]
    amount: Decimal
    tax: Decimal                      # output tax inside this receipt (proportional)
    partial: dict | None = None       # {"invoice": ..., "paid": ..., "open": ...}


class MatchResult(BaseModel):
    bill_for_txn: dict[str, str]                  # bank txn id -> document id
    duplicates: list[tuple[str, str]]             # (duplicate doc, original doc)
    payments: dict[str, InvoicePayment]           # bank txn id -> invoice payment
    unmatched_docs: list[str]
    open_invoices: list[dict]                     # after this month's receipts


def _norm(s: str) -> str:
    s = s.upper()
    s = re.sub(r"\b(PVT|PRIVATE|LTD|LIMITED|LLP|INC|PTE|CO|THE)\b", " ", s)
    return re.sub(r"[^A-Z0-9 ]", " ", s)


def dedupe(docs: list[Document], hashes: dict[str, str]) -> list[tuple[str, str]]:
    seen_hash: dict[str, str] = {}
    seen_key: dict[tuple, str] = {}
    dupes = []
    for d in docs:
        key = (_norm(d.party).strip(), (d.number or "").upper(), d.total)
        original = seen_hash.get(hashes.get(d.id, "")) or (seen_key.get(key) if d.number else None)
        if original:
            dupes.append((d.id, original))
            continue
        seen_hash[hashes.get(d.id, d.id)] = d.id
        seen_key[key] = d.id
    return dupes


def _bill_score(txn: BankTxn, doc: Document, correct_total: Decimal) -> float:
    if abs(-txn.amount - correct_total) > TOL:
        return 0
    if doc.date and not (doc.date - timedelta(days=3) <= txn.date <= doc.date + timedelta(days=25)):
        return 0
    score = fuzz.partial_ratio(_norm(doc.party), _norm(txn.description))
    if doc.number and re.sub(r"\W", "", doc.number.upper()) in re.sub(r"\W", "", txn.description.upper()):
        score += 50
    return score


@tracing.span("TOOL", name="match_bills")
def match_bills(bank: list[BankTxn], docs: list[Document], correct_totals: dict[str, Decimal],
                duplicates: list[tuple[str, str]]) -> dict[str, str]:
    dupe_ids = {d for d, _ in duplicates}
    candidates = []
    for txn in (t for t in bank if t.amount < 0):
        for doc in (d for d in docs if d.id not in dupe_ids):
            s = _bill_score(txn, doc, correct_totals.get(doc.id, doc.total))
            if s >= 45:
                candidates.append((s, txn.id, doc.id))
    used_txn, used_doc, out = set(), set(), {}
    for s, txn_id, doc_id in sorted(candidates, reverse=True):
        if txn_id not in used_txn and doc_id not in used_doc:
            out[txn_id] = doc_id
            used_txn.add(txn_id); used_doc.add(doc_id)
    return out


def _invoice_refs(narration: str, open_numbers: list[str]) -> list[str]:
    text = narration.upper()
    found = [n for n in open_numbers if n.upper() in text]
    if found:
        return found
    tails = re.findall(r"\b(\d{3})\b", text)          # e.g. "KAV034 035 036" / "PART PMT 033"
    tails += re.findall(r"[A-Z](\d{3})\b", text)
    return [n for n in open_numbers if n[-3:] in tails]


@tracing.span("TOOL", name="match_invoice_payments")
def match_payments(bank: list[BankTxn], issued: list[IssuedInvoice]) -> tuple[dict[str, InvoicePayment], list[dict]]:
    open_amt = {i.number: i.total for i in issued}
    by_number = {i.number: i for i in issued}
    payments: dict[str, InvoicePayment] = {}
    for txn in (t for t in bank if t.amount > 0):
        client_invoices = [i for i in issued if fuzz.partial_ratio(_norm(i.client), _norm(txn.description)) >= 80
                           and open_amt[i.number] > 0]
        if not client_invoices:
            continue
        numbers = [i.number for i in client_invoices]
        refs = _invoice_refs(txn.description, numbers)
        chosen = refs
        if not chosen:  # exact subset of the client's open invoices
            for r in range(1, len(numbers) + 1):
                for combo in itertools.combinations(numbers, r):
                    if abs(sum(open_amt[n] for n in combo) - txn.amount) <= TOL:
                        chosen = list(combo); break
                if chosen:
                    break
        if not chosen:
            chosen = [min(client_invoices, key=lambda i: i.date).number]
        due = sum((open_amt[n] for n in chosen), Decimal("0"))
        tax = Decimal("0")
        partial = None
        if abs(due - txn.amount) <= TOL:
            for n in chosen:
                inv = by_number[n]
                tax += inv.tax * open_amt[n] / inv.total
                open_amt[n] = Decimal("0")
        else:  # partial payment against the first referenced invoice
            n = chosen[0]
            inv = by_number[n]
            paid = min(txn.amount, open_amt[n])
            tax += inv.tax * paid / inv.total
            open_amt[n] -= paid
            partial = {"invoice": n, "paid": str(paid), "open": str(open_amt[n])}
            chosen = [n]
        payments[txn.id] = InvoicePayment(bank_txn_id=txn.id, invoices=chosen, amount=txn.amount,
                                          tax=tax.quantize(Decimal("0.01")), partial=partial)
    open_invoices = [{"number": n, "client": by_number[n].client, "date": str(by_number[n].date),
                      "open": str(a), "total": str(by_number[n].total)} for n, a in open_amt.items() if a > 0]
    return payments, open_invoices


def match(bank: list[BankTxn], docs: list[Document], hashes: dict[str, str], correct_totals: dict[str, Decimal],
          issued: list[IssuedInvoice]) -> MatchResult:
    duplicates = dedupe(docs, hashes)
    bills = match_bills(bank, docs, correct_totals, duplicates)
    payments, open_invoices = match_payments(bank, issued)
    matched_docs = set(bills.values()) | {d for d, _ in duplicates}
    return MatchResult(bill_for_txn=bills, duplicates=duplicates, payments=payments,
                       unmatched_docs=[d.id for d in docs if d.id not in matched_docs],
                       open_invoices=open_invoices)
