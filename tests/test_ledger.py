from datetime import date
from decimal import Decimal as D

from munshi import ledger
from munshi.models import BankTxn, Entry

BANK = [
    BankTxn(id="B1", date=date(2026, 9, 2), description="CLIENT ACME", amount=D("118000")),
    BankTxn(id="B2", date=date(2026, 9, 5), description="RZP*FIGMA", amount=D("-1475")),
    BankTxn(id="B3", date=date(2026, 9, 8), description="RENT SEP", amount=D("-45000")),
]
OPEN, CLOSE = D("50000"), D("50000") + D("118000") - D("1475") - D("45000")


def entry(txn_id, account, amount, tax="0"):
    t = next(b for b in BANK if b.id == txn_id)
    return Entry(bank_txn_id=txn_id, date=t.date, payee=t.description, narration="test",
                 account=account, amount=D(amount), tax=D(tax), decided_by="test")


GOOD = [entry("B1", "Income:Services", "118000", "18000"),
        entry("B2", "Expenses:Software", "-1475", "225"),
        entry("B3", "Expenses:Rent", "-45000")]


def close(entries):
    text = ledger.render(entries, OPEN, date(2026, 9, 1), CLOSE, date(2026, 9, 30))
    return ledger.check(text, CLOSE)


def test_good_books_balance():
    r = close(GOOD)
    assert r.ok, r.errors
    assert r.bank_gap == 0


def test_duplicate_is_found_and_repaired():
    bad = GOOD + [entry("B2", "Expenses:Software", "-1475", "225")]
    r = close(bad)
    assert not r.ok and r.bank_gap == D("-1475")
    gaps = ledger.find_gaps(bad, BANK)
    assert [g.kind for g in gaps] == ["duplicate_post"]
    assert close(ledger.repair(bad, gaps, BANK)).ok


def test_missing_post_is_reported():
    gaps = ledger.find_gaps(GOOD[:2], BANK)
    assert [(g.kind, g.bank_txn_id) for g in gaps] == [("missing_post", "B3")]
