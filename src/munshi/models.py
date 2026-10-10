"""Data shapes shared by every step. Money is Decimal, never float."""

import datetime as dt
from decimal import Decimal

from pydantic import BaseModel, Field


class BankTxn(BaseModel):
    id: str                      # stable id, e.g. "B0042"
    date: dt.date
    description: str             # raw narration, e.g. "RZP*ACMETECH 88213"
    amount: Decimal              # + money in, - money out
    balance: Decimal | None = None


class LineItem(BaseModel):
    description: str
    amount: Decimal


class Document(BaseModel):
    id: str                      # e.g. "D0007"
    kind: str                    # "bill" | "receipt" | "invoice_issued"
    party: str                   # vendor or client name as printed
    number: str | None = None
    date: dt.date | None = None
    subtotal: Decimal | None = None
    tax: Decimal = Decimal("0")
    total: Decimal
    currency: str = "INR"
    lines: list[LineItem] = Field(default_factory=list)
    source: str                  # path of the original file


class Entry(BaseModel):
    """One posted transaction: a bank line, its category and the evidence behind it."""

    bank_txn_id: str
    date: dt.date
    payee: str
    narration: str
    account: str                 # e.g. "Expenses:Software"
    amount: Decimal              # same sign convention as the bank line
    tax: Decimal = Decimal("0")  # claimable tax inside `amount` (purchases) or collected (sales)
    document_ids: list[str] = Field(default_factory=list)
    decided_by: str              # "rule:<id>" | "owner" | "llm:<model>" | "crustdata+llm:<model>"
    confidence: float = 1.0
    trace: str | None = None     # neatlogs trace link, when known
