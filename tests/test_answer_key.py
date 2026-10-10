"""The answer key itself must be a valid, balanced set of books."""

import json
from datetime import date
from decimal import Decimal as D
from pathlib import Path

from munshi import ledger
from munshi.models import Entry

KEY = Path(__file__).resolve().parents[1] / "data/answer_key/studio-kaveri-2026-09.json"


def test_answer_key_balances():
    key = json.loads(KEY.read_text(encoding="utf-8"))
    entries = [Entry(bank_txn_id=t["bank_txn_id"], date=date.fromisoformat(t["date"]), payee=t["narration"],
                     narration="answer key", account=t["account"], amount=D(t["amount"]), tax=D(t["tax"]),
                     document_ids=t["documents"], decided_by="answer-key") for t in key["transactions"]]
    closing = D(key["closing_balance"])
    text = ledger.render(entries, D(key["opening_balance"]), date(2026, 9, 1), closing, date(2026, 9, 30))
    result = ledger.check(text, closing)
    assert result.ok, result.errors
    assert result.bank_gap == 0
