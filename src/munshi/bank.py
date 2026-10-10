"""Parse a bank statement export into BankTxn rows. Pure code, no LLM."""

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from munshi import tracing
from munshi.models import BankTxn


def _amount(text: str) -> Decimal:
    text = (text or "").replace(",", "").strip()
    return Decimal(text) if text else Decimal("0")


@tracing.span("TOOL", name="parse_bank_statement")
def parse(path: Path) -> list[BankTxn]:
    """HDFC-style CSV: Date, Narration, Ref No, Withdrawal Amt, Deposit Amt, Closing Balance."""
    rows: list[BankTxn] = []
    with open(path, newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=1):
            amount = _amount(r["Deposit Amt"]) - _amount(r["Withdrawal Amt"])
            rows.append(BankTxn(
                id=r.get("Ref No") or f"B{i:02d}",
                date=datetime.strptime(r["Date"], "%d/%m/%y").date(),
                description=r["Narration"].strip(),
                amount=amount,
                balance=_amount(r["Closing Balance"]),
            ))
    _check_running_balance(rows)
    return rows


def _check_running_balance(rows: list[BankTxn]) -> None:
    """The statement must agree with itself: each balance = previous balance + amount."""
    for prev, cur in zip(rows, rows[1:]):
        if prev.balance is not None and cur.balance is not None and prev.balance + cur.amount != cur.balance:
            raise ValueError(f"Bank statement inconsistent at {cur.id}: {prev.balance} + {cur.amount} != {cur.balance}")


def opening_balance(rows: list[BankTxn]) -> Decimal:
    return rows[0].balance - rows[0].amount


def closing_balance(rows: list[BankTxn]) -> Decimal:
    return rows[-1].balance
