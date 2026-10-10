"""Decide the account for every bank line, with evidence. Order: rules → refunds → documents (LLM)
→ unknown payee via Crustdata (LLM) → ask the owner when still unsure. Never guess silently."""

import json
import re
from decimal import Decimal

from pydantic import BaseModel

from munshi import llm, tracing
from munshi.integrations import crustdata
from munshi.models import BankTxn, Document, Entry

ACCOUNTS = [
    "Income:Services", "Income:Interest",
    "Expenses:Rent", "Expenses:Salaries", "Expenses:Contractors", "Expenses:Software", "Expenses:Hosting",
    "Expenses:Internet", "Expenses:Utilities", "Expenses:Office-Supplies", "Expenses:Meals", "Expenses:Travel",
    "Expenses:Printing", "Expenses:Marketing", "Expenses:Bank-Charges", "Expenses:Professional-Fees",
    "Liabilities:Tax:Collected", "Equity:Owner-Drawings",
]
UNSURE = "Expenses:Uncategorised"

# Generic bank-narration rules (not specific to any one business).
RULES = [
    (r"^SAL\b|SALARY", "Expenses:Salaries", "rule:salary"),
    (r"GST PMT|GST CHALLAN|CPIN", "Liabilities:Tax:Collected", "rule:gst-payment"),
    (r"CHGS|CHARGES|SMS ALERT", "Expenses:Bank-Charges", "rule:bank-charges"),
    (r"^INT CR|INTEREST", "Income:Interest", "rule:interest"),
]


class Question(BaseModel):
    bank_txn_id: str
    text: str
    suggestion: str | None = None


DOC_PROMPT = """You are a careful bookkeeper. Choose the ONE best account for this business expense.
Allowed accounts: {accounts}
Reply with JSON: {{"account": "...", "reason": "one short sentence", "confidence": 0.0-1.0}}"""

PAYEE_PROMPT = """From a bank narration, extract the merchant/company being paid.
Reply with JSON: {"company": "name as best you can tell", "domain_guess": "e.g. notion.com or null"}"""

UNKNOWN_PROMPT = """You are a careful bookkeeper for a design studio. Choose the account for this bank payment.
If it could plausibly be personal or you are not sure, set confidence below 0.6.
Allowed accounts: {accounts}
Reply with JSON: {{"account": "...", "reason": "one short sentence", "confidence": 0.0-1.0}}"""


def _valid(account: str) -> str:
    return account if account in ACCOUNTS else UNSURE


@tracing.span("AGENT", name="categorise")
def categorise(txn: BankTxn, doc: Document | None, vendor_error: bool, earlier: list[Entry],
               owner_answers: dict, non_claimable: set[str]) -> tuple[Entry, Question | None]:
    base = dict(bank_txn_id=txn.id, date=txn.date, payee=txn.description, amount=txn.amount)
    text = txn.description.upper()

    for pattern, account, rule_id in RULES:
        if re.search(pattern, text):
            return Entry(**base, narration=f"{account.split(':')[-1]} ({rule_id})", account=account,
                         decided_by=rule_id), None

    for key, ans in owner_answers.items():
        if key.upper() in text:
            return Entry(**base, narration=ans.get("answer", "owner answer"), account=ans["account"],
                         decided_by="owner"), None

    if re.search(r"\bRFND\b|REFUND|REVERSAL", text) and txn.amount > 0:
        payee = re.sub(r"\bRFND\b|REFUND|REVERSAL", "", text).strip()
        prior = next((e for e in earlier if e.amount < 0 and payee[:10] in e.payee.upper()), None)
        if prior:
            return Entry(**base, narration=f"Refund from vendor (reverses {prior.bank_txn_id})",
                         account=prior.account, decided_by=f"rule:refund-of:{prior.bank_txn_id}"), None

    if doc is not None:
        lines = "; ".join(f"{li.description} {li.amount}" for li in doc.lines) or "(no line items)"
        r = llm.ask_json("cheap", DOC_PROMPT.format(accounts=", ".join(ACCOUNTS)),
                         f"Vendor: {doc.party}\nLines: {lines}\nBank narration: {txn.description}")
        account = _valid(r.get("account", ""))
        tax = Decimal("0")
        if doc.tax and account not in non_claimable:
            tax = doc.tax
        note = r.get("reason", "")
        if vendor_error:
            note += f" | vendor bill total printed as {doc.total}; paid correct amount"
        entry = Entry(**base, narration=note, account=account, tax=tax, document_ids=[doc.id],
                      decided_by=f"llm:{llm.model_for('cheap')}", confidence=float(r.get("confidence", 0.8)))
        return entry, None

    # No document: work out who was paid, then decide.
    who = llm.ask_json("cheap", PAYEE_PROMPT, txn.description)
    company = crustdata.resolve(who.get("company") or txn.description, who.get("domain_guess"))
    context = json.dumps({k: company.get(k) for k in ("name", "domain", "industries", "description")}) if company else "no company data found"
    r = llm.ask_json("cheap", UNKNOWN_PROMPT.format(accounts=", ".join(ACCOUNTS)),
                     f"Bank narration: {txn.description}\nAmount: {txn.amount}\nCompany data (Crustdata): {context}")
    account, conf = _valid(r.get("account", "")), float(r.get("confidence", 0.5))
    decided = f"crustdata+llm:{llm.model_for('cheap')}" if company else f"llm:{llm.model_for('cheap')}"
    if conf < 0.6 or account == UNSURE:
        q = Question(bank_txn_id=txn.id, suggestion=account,
                     text=f"₹{abs(txn.amount):,} '{txn.description}' on {txn.date:%d %b}: what was this for?")
        return Entry(**base, narration="waiting for owner", account=UNSURE, decided_by=decided, confidence=conf), q
    name = company["name"] if company else who.get("company")
    return Entry(**base, narration=f"{name}: {r.get('reason', '')}", account=account, decided_by=decided,
                 confidence=conf), None


def income_entry(txn: BankTxn, invoices: list[str], tax: Decimal, partial: dict | None) -> Entry:
    note = f"Client payment for {', '.join(invoices)}"
    if partial:
        note += f" (partial: {partial['open']} still open on {partial['invoice']})"
    return Entry(bank_txn_id=txn.id, date=txn.date, payee=txn.description, narration=note,
                 account="Income:Services", amount=txn.amount, tax=tax, document_ids=invoices,
                 decided_by="match:issued-invoices")
