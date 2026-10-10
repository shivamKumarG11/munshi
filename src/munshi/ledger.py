"""Books as code: write a beancount ledger, validate it, and hunt for gaps against the bank.

Everything here is deterministic. The LLM never decides whether the books balance.
"""

from collections import Counter
from datetime import date, timedelta
from decimal import Decimal

from beancount import loader
from pydantic import BaseModel

from munshi.models import BankTxn, Entry

BANK = "Assets:Bank:Current"
OPENING = "Equity:Opening-Balances"
TAX_INPUT = "Assets:Tax:Input-Credit"      # tax paid on purchases (claimable)
TAX_OUTPUT = "Liabilities:Tax:Collected"   # tax collected on sales


def _q(s: str) -> str:
    return s.replace("\\", "/").replace('"', "'")


def render(entries: list[Entry], opening_balance: Decimal, period_start: date,
           closing_balance: Decimal, period_end: date, currency: str = "INR") -> str:
    """Render the month as beancount text, ending with a balance assertion against the bank."""
    accounts = sorted({e.account for e in entries} | {BANK, OPENING, TAX_INPUT, TAX_OUTPUT})
    opened = period_start - timedelta(days=1)
    out = [f'option "operating_currency" "{currency}"', ""]
    out += [f"{opened} open {a}" for a in accounts]
    out += ["", f'{opened} * "Opening balance"', f"  {BANK}  {opening_balance} {currency}", f"  {OPENING}", ""]

    for e in sorted(entries, key=lambda x: (x.date, x.bank_txn_id)):
        out.append(f'{e.date} * "{_q(e.payee)}" "{_q(e.narration)}"')
        out.append(f'  bank_txn: "{e.bank_txn_id}"')
        if e.document_ids:
            out.append(f'  documents: "{",".join(e.document_ids)}"')
        out.append(f'  decided_by: "{_q(e.decided_by)}"')
        out.append(f'  confidence: "{e.confidence:.2f}"')
        if e.trace:
            out.append(f'  trace: "{e.trace}"')
        # Bank side carries the real cash movement; the other side is category (+ tax split).
        out.append(f"  {BANK}  {e.amount} {currency}")
        if e.tax:
            tax_account = TAX_INPUT if e.amount < 0 else TAX_OUTPUT
            out.append(f"  {tax_account}  {e.tax if e.amount < 0 else -e.tax} {currency}")
            out.append(f"  {e.account}  {-(e.amount) - (e.tax if e.amount < 0 else -e.tax)} {currency}")
        else:
            out.append(f"  {e.account}  {-e.amount} {currency}")
        out.append("")

    out.append(f"{period_end + timedelta(days=1)} balance {BANK}  {closing_balance} {currency}")
    return "\n".join(out) + "\n"


class CheckResult(BaseModel):
    ok: bool
    errors: list[str]
    bank_gap: Decimal                # ledger closing bank balance - statement closing balance


def check(text: str, closing_balance: Decimal) -> CheckResult:
    """Validate with beancount: every transaction balances, and the bank balance assertion holds."""
    entries, errors, _ = loader.load_string(text)
    messages = [e.message for e in errors]
    ledger_bank = Decimal("0")
    for entry in entries:
        for posting in getattr(entry, "postings", None) or []:
            if posting.account == BANK and posting.units is not None:
                ledger_bank += posting.units.number
    return CheckResult(ok=not messages, errors=messages, bank_gap=ledger_bank - closing_balance)


class Gap(BaseModel):
    kind: str          # "duplicate_post" | "missing_post" | "amount_mismatch" | "unknown_txn"
    bank_txn_id: str
    detail: str
    effect: Decimal    # how much this explains of the bank gap


def find_gaps(entries: list[Entry], bank: list[BankTxn]) -> list[Gap]:
    """Compare what was posted to what the bank says happened, line by line."""
    by_id = {t.id: t for t in bank}
    posted = Counter(e.bank_txn_id for e in entries)
    gaps: list[Gap] = []
    for txn_id, n in posted.items():
        txn = by_id.get(txn_id)
        if txn is None:
            amount = sum((e.amount for e in entries if e.bank_txn_id == txn_id), Decimal("0"))
            gaps.append(Gap(kind="unknown_txn", bank_txn_id=txn_id, effect=amount,
                            detail=f"posted {n}x but no such bank line"))
        elif n > 1:
            gaps.append(Gap(kind="duplicate_post", bank_txn_id=txn_id, effect=txn.amount * (n - 1),
                            detail=f"'{txn.description}' {txn.amount} posted {n} times"))
    for txn in bank:
        if txn.id not in posted:
            gaps.append(Gap(kind="missing_post", bank_txn_id=txn.id, effect=-txn.amount,
                            detail=f"'{txn.description}' {txn.amount} on {txn.date} never posted"))
        else:
            posted_sum = sum((e.amount for e in entries if e.bank_txn_id == txn.id), Decimal("0"))
            expected = txn.amount * posted[txn.id]
            if posted_sum != expected:
                gaps.append(Gap(kind="amount_mismatch", bank_txn_id=txn.id, effect=posted_sum - expected,
                                detail=f"bank says {txn.amount}, ledger has {posted_sum / posted[txn.id]}"))
    return gaps


def repair(entries: list[Entry], gaps: list[Gap], bank: list[BankTxn]) -> list[Entry]:
    """Apply only the fixes that are certain: drop duplicate posts and posts for unknown lines,
    and correct amounts to the bank's figure. Missing posts need categorising, so they're returned
    to the caller (the coordinator sends them back through the categoriser)."""
    by_id = {t.id: t for t in bank}
    drop_dupes = {g.bank_txn_id for g in gaps if g.kind == "duplicate_post"}
    drop_unknown = {g.bank_txn_id for g in gaps if g.kind == "unknown_txn"}
    fix_amount = {g.bank_txn_id for g in gaps if g.kind == "amount_mismatch"}
    seen: set[str] = set()
    fixed: list[Entry] = []
    for e in entries:
        if e.bank_txn_id in drop_unknown:
            continue
        if e.bank_txn_id in drop_dupes:
            if e.bank_txn_id in seen:
                continue
            seen.add(e.bank_txn_id)
        if e.bank_txn_id in fix_amount:
            e = e.model_copy(update={"amount": by_id[e.bank_txn_id].amount})
        fixed.append(e)
    return fixed
