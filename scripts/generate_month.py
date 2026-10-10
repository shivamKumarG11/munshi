"""Generate the demo month for Studio Kaveri (a fictional Bengaluru design studio), September 2026.

GENERATED DATA, labelled as such. All vendor and client names are fictional. Bank narrations for
two real companies (Notion, Netflix) are only payment descriptions; no documents are faked for them.

Writes:
  data/demo/studio-kaveri/2026-09/
    bank_statement.csv          the month's bank export
    timesheet.csv               hours worked per client
    invoices_issued.csv         invoices Studio Kaveri sent (incl. older unpaid ones)
    documents/                  bills (PDF) and receipts (PNG photos, one rotated and blurred)
  data/answer_key/studio-kaveri-2026-09.json
"""

import csv
import json
import shutil
from datetime import date
from decimal import Decimal as D
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/demo/studio-kaveri/2026-09"
DOCS = OUT / "documents"
KEY = ROOT / "data/answer_key/studio-kaveri-2026-09.json"

BUSINESS = {
    "name": "Studio Kaveri Design LLP",
    "gstin": "29ABCFS1234K1Z5",
    "address": "3rd Floor, 80 Feet Road, Koramangala, Bengaluru 560034",
    "bank": "HDFC Bank current account XX4421",
}
OPENING = D("650000.00")
GST = D("0.18")


def money(x: D) -> str:
    return f"{x:,.2f}"


# --------------------------------------------------------------------------- documents

def bill_pdf(path: Path, vendor: dict, number: str, day: date, lines: list[tuple[str, D]],
             tax_rate: D = GST, printed_total: D | None = None) -> dict:
    """A vendor bill. `printed_total` lets us plant a vendor arithmetic error."""
    subtotal = sum((amt for _, amt in lines), D("0"))
    tax = (subtotal * tax_rate).quantize(D("0.01"))
    total = printed_total if printed_total is not None else subtotal + tax
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    y = h - 60
    c.setFont("Helvetica-Bold", 16); c.drawString(50, y, vendor["name"]); y -= 18
    c.setFont("Helvetica", 9)
    c.drawString(50, y, vendor["address"]); y -= 12
    if vendor.get("gstin"):
        c.drawString(50, y, f"GSTIN: {vendor['gstin']}"); y -= 12
    y -= 10
    c.setFont("Helvetica-Bold", 13); c.drawString(50, y, "TAX INVOICE" if tax_rate else "BILL"); y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Invoice No: {number}"); c.drawString(330, y, f"Date: {day:%d-%m-%Y}"); y -= 14
    c.drawString(50, y, f"Bill to: {BUSINESS['name']}"); y -= 12
    c.drawString(50, y, BUSINESS["address"]); y -= 12
    c.drawString(50, y, f"Buyer GSTIN: {BUSINESS['gstin']}"); y -= 24
    c.setFont("Helvetica-Bold", 10); c.drawString(50, y, "Description"); c.drawRightString(540, y, "Amount (INR)"); y -= 6
    c.line(50, y, 540, y); y -= 14
    c.setFont("Helvetica", 10)
    for desc, amt in lines:
        c.drawString(50, y, desc); c.drawRightString(540, y, money(amt)); y -= 14
    c.line(50, y + 4, 540, y + 4); y -= 10
    c.drawString(330, y, "Subtotal"); c.drawRightString(540, y, money(subtotal)); y -= 14
    if tax_rate:
        half = (tax / 2).quantize(D("0.01"))
        c.drawString(330, y, "CGST 9%"); c.drawRightString(540, y, money(half)); y -= 14
        c.drawString(330, y, "SGST 9%"); c.drawRightString(540, y, money(tax - half)); y -= 14
    c.setFont("Helvetica-Bold", 11)
    c.drawString(330, y, "TOTAL"); c.drawRightString(540, y, money(total)); y -= 30
    c.setFont("Helvetica", 8); c.drawString(50, y, "Payment due within 15 days. Thank you for your business.")
    c.save()
    return {"party": vendor["name"], "number": number, "date": str(day), "subtotal": str(subtotal),
            "tax": str(tax), "total": str(total), "correct_total": str(subtotal + tax)}


def receipt_png(path: Path, shop: str, address: str, day: date, items: list[tuple[str, D]],
                messy: bool = False) -> dict:
    """A shop receipt as a phone photo. `messy` = rotated, blurred, low contrast."""
    total = sum((amt for _, amt in items), D("0"))
    img = Image.new("L", (420, 120 + 26 * (len(items) + 6)), 250)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("cour.ttf", 16)
        bold = ImageFont.truetype("courbd.ttf", 18)
    except OSError:
        font = bold = ImageFont.load_default()
    y = 16
    d.text((20, y), shop, font=bold, fill=10); y += 26
    d.text((20, y), address, font=font, fill=40); y += 22
    d.text((20, y), f"Date: {day:%d/%m/%Y}", font=font, fill=20); y += 30
    for name, amt in items:
        d.text((20, y), f"{name:<22}{money(amt):>12}", font=font, fill=20); y += 26
    d.text((20, y), "-" * 34, font=font, fill=60); y += 22
    d.text((20, y), f"{'TOTAL (incl. GST)':<22}{money(total):>12}", font=bold, fill=0); y += 30
    d.text((20, y), "Thank you! Visit again", font=font, fill=60)
    if messy:
        img = img.rotate(9, expand=True, fillcolor=235).filter(ImageFilter.GaussianBlur(1.6))
        img = img.point(lambda p: 90 + p * 0.55)
    img.convert("RGB").save(path)
    return {"party": shop, "date": str(day), "total": str(total)}


# --------------------------------------------------------------------------- the month

def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    DOCS.mkdir(parents=True)
    KEY.parent.mkdir(parents=True, exist_ok=True)

    vendors = {
        "rent": {"name": "Koramangala Workspaces LLP", "address": "47 Hosur Road, Bengaluru 560095", "gstin": "29AAKFK4521M1Z2"},
        "isp": {"name": "Skyline Fibernet Pvt Ltd", "address": "12 Residency Road, Bengaluru 560025", "gstin": "29AAJCS7788P1ZQ"},
        "cloud": {"name": "CloudNest Hosting Pvt Ltd", "address": "Sector 5, HSR Layout, Bengaluru 560102", "gstin": "29AAGCC3310L1Z9"},
        "print": {"name": "PrintWorks Studio", "address": "22 Church Street, Bengaluru 560001", "gstin": "29ABGPP6612R1ZA"},
        "tools": {"name": "Pixelforge Design Tools Pte Ltd", "address": "1 Raffles Place, Singapore 048616", "gstin": None},
        "power": {"name": "Metro Power Distribution Co", "address": "KR Circle, Bengaluru 560001", "gstin": None},
    }

    docs = {}  # doc id -> metadata (answer key)

    def add_doc(doc_id, filename, meta, kind):
        docs[doc_id] = {"file": f"documents/{filename}", "kind": kind, **meta}

    add_doc("D01", "koramangala-workspaces-sep.pdf",
            bill_pdf(DOCS / "koramangala-workspaces-sep.pdf", vendors["rent"], "KW/2026/0912", date(2026, 9, 1),
                     [("Office rent - September 2026 (6 seats)", D("50000.00"))]), "bill")
    add_doc("D02", "skyline-fibernet-sep.pdf",
            bill_pdf(DOCS / "skyline-fibernet-sep.pdf", vendors["isp"], "SFN-88213-09", date(2026, 9, 3),
                     [("Business broadband 300 Mbps - Sep 2026", D("1999.00"))]), "bill")
    cloud = bill_pdf(DOCS / "cloudnest-hosting-sep.pdf", vendors["cloud"], "CN-INV-20419", date(2026, 9, 5),
                     [("Managed hosting - client sites (Sep)", D("6500.00")), ("Daily backups", D("1000.00"))])
    add_doc("D03", "cloudnest-hosting-sep.pdf", cloud, "bill")
    # TRAP 1: the same bill uploaded twice under another filename
    shutil.copy(DOCS / "cloudnest-hosting-sep.pdf", DOCS / "IMG_cloudnest_invoice_copy.pdf")
    add_doc("D04", "IMG_cloudnest_invoice_copy.pdf", {**cloud, "duplicate_of": "D03"}, "bill")
    # TRAP 8: vendor arithmetic error. Lines 3,000 + 2,000; GST 900; printed total 6,100 (correct 5,900)
    add_doc("D05", "printworks-studio-0917.pdf",
            bill_pdf(DOCS / "printworks-studio-0917.pdf", vendors["print"], "PWS-1177", date(2026, 9, 17),
                     [("Brand booklets, 200 copies (Zenith Foods)", D("3000.00")), ("Lamination", D("2000.00"))],
                     printed_total=D("6100.00")), "bill")
    add_doc("D06", "pixelforge-annual-seat.pdf",
            bill_pdf(DOCS / "pixelforge-annual-seat.pdf", vendors["tools"], "PXF-2026-55102", date(2026, 9, 9),
                     [("Pixelforge Pro - 1 seat, monthly", D("2950.00"))], tax_rate=D("0")), "bill")
    add_doc("D07", "metro-power-aug-sep.pdf",
            bill_pdf(DOCS / "metro-power-aug-sep.pdf", vendors["power"], "MPD-7731902", date(2026, 9, 12),
                     [("Electricity 412 units (12 Aug - 11 Sep)", D("4820.00"))], tax_rate=D("0")), "bill")
    # TRAP 7: a messy phone photo of a receipt
    add_doc("D08", "receipt_photo_0915.png",
            receipt_png(DOCS / "receipt_photo_0915.png", "BRIGHTLINE STATIONERS", "Koramangala 5th Block",
                        date(2026, 9, 15), [("A3 sketch pads x4", D("720.00")), ("Markers set", D("460.00"))],
                        messy=True), "receipt")
    add_doc("D09", "receipt_lunch_0922.png",
            receipt_png(DOCS / "receipt_lunch_0922.png", "UDUPI GRAND RESTAURANT", "80 Feet Rd, Koramangala",
                        date(2026, 9, 22), [("Team lunch (6 pax)", D("2100.00")), ("Beverages", D("350.00"))]),
            "receipt")

    # Invoices Studio Kaveri issued (sales). Amounts include 18% GST.
    issued = [
        {"number": "KAV-2026-029", "client": "Orbit Logistics Pvt Ltd", "date": "2026-08-03", "subtotal": "120000.00"},  # TRAP 10 overdue
        {"number": "KAV-2026-031", "client": "Acme Retail Pvt Ltd", "date": "2026-08-25", "subtotal": "100000.00"},
        {"number": "KAV-2026-033", "client": "Zenith Foods Pvt Ltd", "date": "2026-08-28", "subtotal": "75000.00"},     # TRAP 4 partial
        {"number": "KAV-2026-034", "client": "Nimbus Health Pvt Ltd", "date": "2026-08-30", "subtotal": "80000.00"},    # TRAP 3 one-to-many
        {"number": "KAV-2026-035", "client": "Nimbus Health Pvt Ltd", "date": "2026-09-04", "subtotal": "70000.00"},
        {"number": "KAV-2026-036", "client": "Nimbus Health Pvt Ltd", "date": "2026-09-10", "subtotal": "50000.00"},
    ]
    for inv in issued:
        sub = D(inv["subtotal"])
        inv["tax"] = str((sub * GST).quantize(D("0.01")))
        inv["total"] = str(sub + D(inv["tax"]))
    with open(OUT / "invoices_issued.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["number", "client", "date", "subtotal", "tax", "total"])
        w.writeheader(); w.writerows(issued)

    # Timesheet. TRAP 9: Zenith Foods September sprint was never invoiced.
    timesheet = [
        ("2026-09", "Acme Retail Pvt Ltd", "Website refresh - phase 2", 18, "invoiced:KAV-2026-031"),
        ("2026-09", "Nimbus Health Pvt Ltd", "Patient app UI", 96, "invoiced:KAV-2026-035,KAV-2026-036"),
        ("2026-09", "Zenith Foods Pvt Ltd", "Packaging design sprint", 40, "not invoiced"),
    ]
    with open(OUT / "timesheet.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["month", "client", "project", "hours", "billing_status"]); w.writerows(timesheet)

    # Bank statement: (id, date, narration, amount, account, tax, documents, trap note)
    t = [
        ("B01", date(2026, 9, 1), "NEFT-KORAMANGALA WORKSPACES LLP-KW2026 0912", D("-59000.00"), "Expenses:Rent", D("9000.00"), ["D01"], None),
        ("B02", date(2026, 9, 2), "NEFT CR-ACME RETAIL PVT LTD-INV KAV-2026-031", D("118000.00"), "Income:Services", D("18000.00"), [], "invoice KAV-2026-031 paid in full"),
        ("B03", date(2026, 9, 3), "SAL SEP-ANANYA RAO", D("-72000.00"), "Expenses:Salaries", D("0"), [], None),
        ("B04", date(2026, 9, 3), "SAL SEP-VIKRAM NAIR", D("-65000.00"), "Expenses:Salaries", D("0"), [], None),
        ("B05", date(2026, 9, 3), "SAL SEP-MEERA IYER", D("-58000.00"), "Expenses:Salaries", D("0"), [], None),
        ("B06", date(2026, 9, 4), "SKYLINE FIBERNET AUTOPAY SFN88213", D("-2358.82"), "Expenses:Internet", D("359.82"), ["D02"], None),
        ("B07", date(2026, 9, 6), "UPI-CLOUDNEST HOSTING-CNINV20419", D("-8850.00"), "Expenses:Hosting", D("1350.00"), ["D03"], "TRAP 1: D04 is a duplicate upload of D03"),
        ("B08", date(2026, 9, 8), "RZP*NOTION LABS 88213", D("-2950.00"), "Expenses:Software", D("0"), [], "TRAP 2+6: cryptic payee (Notion) and no bill: not claimable yet"),
        ("B09", date(2026, 9, 9), "POS INTL PIXELFORGE PTE SINGAPORE", D("-2950.00"), "Expenses:Software", D("0"), ["D06"], None),
        ("B10", date(2026, 9, 10), "GST PMT CHALLAN CPIN 2608290012", D("-31000.00"), "Liabilities:Tax:Collected", D("0"), [], "August GST paid to government"),
        ("B11", date(2026, 9, 11), "IMPS-R SHARMA-ILLUSTRATIONS", D("-12000.00"), "Expenses:Contractors", D("0"), [], "owner question: contractor (owner confirms)"),
        ("B12", date(2026, 9, 12), "NEFT CR-ZENITH FOODS PVT LTD-PART PMT 033", D("50000.00"), "Income:Services", D("7627.12"), [], "TRAP 4: partial payment of KAV-2026-033 (88,500); 38,500 still open"),
        ("B13", date(2026, 9, 14), "BBPS-METRO POWER DIST-7731902", D("-4820.00"), "Expenses:Utilities", D("0"), ["D07"], None),
        ("B14", date(2026, 9, 15), "UPI-BRIGHTLINE STATIONERS", D("-1180.00"), "Expenses:Office-Supplies", D("0"), ["D08"], "TRAP 7: receipt photo is rotated and blurred; no GST breakdown, so no input credit"),
        ("B15", date(2026, 9, 16), "RFND PIXELFORGE PTE SINGAPORE", D("590.00"), "Expenses:Software", D("0"), [], "TRAP 5: vendor refund, reduces Software expense (not income)"),
        ("B16", date(2026, 9, 18), "NEFT CR-NIMBUS HEALTH PVT LTD-KAV034 035 036", D("236000.00"), "Income:Services", D("36000.00"), [], "TRAP 3: one payment for three invoices (94,400 + 82,600 + 59,000)"),
        ("B17", date(2026, 9, 19), "UPI-PRINTWORKS STUDIO-PWS1177", D("-5900.00"), "Expenses:Printing", D("900.00"), ["D05"], "TRAP 8: bill total printed as 6,100, correct total and payment 5,900"),
        ("B18", date(2026, 9, 21), "NETFLIX.COM SUBSCRIPTION", D("-649.00"), "Equity:Owner-Drawings", D("0"), [], "TRAP 12: personal expense on business account (owner confirms)"),
        ("B19", date(2026, 9, 22), "UPI-UDUPI GRAND RESTAURANT", D("-2450.00"), "Expenses:Meals", D("0"), ["D09"], "meals: GST shown but not claimable"),
        ("B20", date(2026, 9, 30), "SMS ALERT CHGS SEP", D("-59.00"), "Expenses:Bank-Charges", D("0"), [], None),
        ("B21", date(2026, 9, 30), "INT CR SWEEP FD", D("1312.00"), "Income:Interest", D("0"), [], None),
    ]

    balance = OPENING
    with open(OUT / "bank_statement.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Narration", "Ref No", "Withdrawal Amt", "Deposit Amt", "Closing Balance"])
        for txn_id, day, narration, amount, *_ in t:
            balance += amount
            w.writerow([f"{day:%d/%m/%y}", narration, txn_id,
                        f"{-amount:.2f}" if amount < 0 else "", f"{amount:.2f}" if amount > 0 else "", f"{balance:.2f}"])
    closing = balance

    # Tax-to-set-aside (estimate from configured assumptions)
    output_tax = sum((tax for _, _, _, amt, acct, tax, _, _ in t if acct == "Income:Services"), D("0"))
    input_tax = sum((tax for _, _, _, amt, acct, tax, _, _ in t if amt < 0 and tax > 0), D("0"))

    key = {
        "label": "GENERATED demo data: fictional business, vendors and clients",
        "business": BUSINESS,
        "period": {"start": "2026-09-01", "end": "2026-09-30"},
        "opening_balance": str(OPENING),
        "closing_balance": str(closing),
        "tax_assumptions": {"gst_rate": "0.18", "income_tax_provision_rate": "0.25",
                            "note": "Meals GST not claimable; foreign SaaS without GSTIN: no input credit"},
        "expected_tax": {"output_tax_collected": str(output_tax), "input_tax_claimable": str(input_tax),
                         "net_indirect_tax": str(output_tax - input_tax)},
        "transactions": [
            {"bank_txn_id": i, "date": str(d_), "narration": n, "amount": str(a), "account": acct,
             "tax": str(tax), "documents": dl, "note": note}
            for i, d_, n, a, acct, tax, dl, note in t
        ],
        "documents": docs,
        "open_items": {
            "missing_bills": ["B08"],
            "duplicate_documents": [["D04", "D03"]],
            "vendor_errors": [{"doc": "D05", "printed_total": "6100.00", "correct_total": "5900.00"}],
            "partial_payments": [{"invoice": "KAV-2026-033", "paid": "50000.00", "open": "38500.00"}],
            "overdue_invoices": [{"invoice": "KAV-2026-029", "client": "Orbit Logistics Pvt Ltd", "total": "141600.00",
                                  "days_overdue_at_month_end": (date(2026, 9, 30) - date(2026, 8, 3)).days - 15}],
            "uninvoiced_work": [{"client": "Zenith Foods Pvt Ltd", "project": "Packaging design sprint", "hours": 40}],
            "owner_questions": ["B11", "B18"],
        },
        "matches": {"B02": ["KAV-2026-031"], "B12": ["KAV-2026-033"], "B16": ["KAV-2026-034", "KAV-2026-035", "KAV-2026-036"]},
    }
    KEY.write_text(json.dumps(key, indent=2), encoding="utf-8")
    # What the owner answers when Munshi asks (in the app the owner taps these live).
    (OUT / "owner_answers.json").write_text(json.dumps({
        "R SHARMA": {"account": "Expenses:Contractors", "answer": "Freelance illustrator for the Nimbus app"},
        "NETFLIX": {"account": "Equity:Owner-Drawings", "answer": "Personal, my mistake"},
    }, indent=2), encoding="utf-8")
    (OUT / "business.json").write_text(json.dumps({
        **BUSINESS, "industry": "Design and digital product studio", "peer_sics": ["7311", "8742"],
        "hourly_rate": "2000.00", "gst_rate": "0.18", "income_tax_provision_rate": "0.25",
        "payment_terms_days": 15, "non_claimable_tax_accounts": ["Expenses:Meals"],
        "client_emails": {"Zenith Foods Pvt Ltd": "accounts@zenithfoods.example",
                          "Orbit Logistics Pvt Ltd": "ap@orbitlogistics.example"},
    }, indent=2), encoding="utf-8")
    (OUT / "README.md").write_text(
        "# Studio Kaveri: September 2026 (GENERATED demo data)\n\n"
        "Fictional business, vendors and clients. Generated by `scripts/generate_month.py`.\n"
        "Munshi's document reader is benchmarked separately on real receipts (`data/benchmark/sroie`).\n",
        encoding="utf-8")
    print(f"{len(t)} bank lines, {len(docs)} documents, opening {OPENING}, closing {closing}")
    print(f"tax: output {output_tax}, input {input_tax}, net {output_tax - input_tax}")


if __name__ == "__main__":
    build()
