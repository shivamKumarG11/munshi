"""Read bills and receipts into Document records.

Cheap model first; arithmetic is checked in code; only documents that fail the checks are re-read
with the strong model. If the strong model reads the same numbers, the document itself is wrong
(a vendor error) and is flagged, never silently "fixed".
"""

import hashlib
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pdfplumber
from pydantic import BaseModel

from munshi import llm, tracing
from munshi.models import Document, LineItem

SYSTEM = """You extract data from business documents (bills, invoices, receipts).
Return ONLY a JSON object with these keys:
  party: the seller's business name exactly as printed at the top (no branch, address or registration number)
  number: invoice/bill number or null
  date: YYYY-MM-DD or null
  subtotal: amount before tax as a plain number, or null
  tax: total tax amount as a plain number (0 if none shown)
  total: the final amount payable as printed (after any rounding adjustment; do not recompute it)
  currency: ISO code if visible, else null
  lines: list of {description, amount}
Copy numbers exactly as printed. Never invent values; use null when unsure."""

TOLERANCE = Decimal("0.02")


class ReadResult(BaseModel):
    document: Document
    issues: list[str]            # arithmetic problems found in code
    model_role: str              # which model produced the final reading
    vendor_error: bool = False   # both models agree on numbers that don't add up
    content_hash: str            # identical files share a hash (duplicate uploads)


def _dec(value) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(re.sub(r"[^\d.\-]", "", str(value)))
    except InvalidOperation:
        return None


def check(doc: Document) -> list[str]:
    """Arithmetic only. Returns human-readable problems (empty = consistent)."""
    issues = []
    if doc.lines and doc.subtotal is not None:
        line_sum = sum((li.amount for li in doc.lines), Decimal("0"))
        if abs(line_sum - doc.subtotal) > TOLERANCE:
            issues.append(f"line items add to {line_sum}, subtotal says {doc.subtotal}")
    if doc.subtotal is not None and abs(doc.subtotal + doc.tax - doc.total) > TOLERANCE:
        issues.append(f"subtotal {doc.subtotal} + tax {doc.tax} = {doc.subtotal + doc.tax}, total says {doc.total}")
    if doc.subtotal is None and doc.lines:
        line_sum = sum((li.amount for li in doc.lines), Decimal("0"))
        if abs(line_sum - doc.total) > TOLERANCE and abs(line_sum + doc.tax - doc.total) > TOLERANCE:
            issues.append(f"line items add to {line_sum}, total says {doc.total}")
    return issues


def _date(value):
    """Models return dates in many formats; never let one crash the read."""
    if not value:
        return None
    from datetime import datetime
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%d/%m/%y", "%d-%m-%y", "%d.%m.%y",
                "%d %b %Y", "%d %b %y", "%d %B %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(text[:20].strip(), fmt).date()
        except ValueError:
            continue
    return None


def _to_document(raw: dict, doc_id: str, kind: str, source: Path) -> Document:
    return Document(
        id=doc_id, kind=kind, source=str(source).replace("\\", "/"),
        party=(raw.get("party") or "UNKNOWN").strip(),
        number=raw.get("number"),
        date=_date(raw.get("date")),
        subtotal=_dec(raw.get("subtotal")),
        tax=_dec(raw.get("tax")) or Decimal("0"),
        total=_dec(raw.get("total")) or Decimal("0"),
        currency=raw.get("currency") or "INR",
        lines=[LineItem(description=li.get("description", ""), amount=_dec(li.get("amount")) or Decimal("0"))
               for li in raw.get("lines") or [] if _dec(li.get("amount")) is not None],
    )


def _extract(path: Path, role: str) -> dict:
    if path.suffix.lower() == ".pdf":
        with pdfplumber.open(path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        if text.strip():
            return llm.ask_json(role, SYSTEM, f"Document text:\n\n{text}")
        role = "vision" if role == "cheap" else role
        images = _render_pdf(path)
        return llm.ask_json(role, SYSTEM, "Extract the document shown.", images=images)
    vision_role = "vision" if role == "cheap" else role
    return llm.ask_json(vision_role, SYSTEM, "Extract the document shown in this photo.", images=[path])


def _render_pdf(path: Path) -> list[Path]:
    out = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages[:2]):
            img_path = path.with_suffix(f".page{i}.png")
            page.to_image(resolution=150).save(img_path)
            out.append(img_path)
    return out


@tracing.span("AGENT", name="read_document")
def read(path: Path, doc_id: str, kind: str = "bill") -> ReadResult:
    content_hash = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    doc = _to_document(_extract(path, "cheap"), doc_id, kind, path)
    issues = check(doc)
    if not issues:
        return ReadResult(document=doc, issues=[], model_role="cheap", content_hash=content_hash)

    # Recovery: re-read with the strong model and compare.
    second = _to_document(_extract(path, "strong"), doc_id, kind, path)
    second_issues = check(second)
    if not second_issues:
        return ReadResult(document=second, issues=[], model_role="strong", content_hash=content_hash)
    same_numbers = (second.subtotal, second.tax, second.total) == (doc.subtotal, doc.tax, doc.total)
    return ReadResult(document=second, issues=second_issues, model_role="strong",
                      vendor_error=same_numbers, content_hash=content_hash)
