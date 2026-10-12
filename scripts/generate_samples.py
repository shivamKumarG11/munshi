"""Build samples/: three complete demo businesses you can feed to Munshi, each with late-arriving files.

GENERATED DATA, labelled as such. Every business, vendor, client and person is fictional. A few bank
narrations name real companies (e.g. Notion, Figma) only as payment descriptions; no documents are
ever faked for real companies.

samples/<scenario>/
  business.json, owner_answers.json        who the business is; what the owner answers when asked
  bank_statement.csv                       the month's bank export
  invoices_issued.csv, timesheet.csv       sales invoices sent; hours worked (when relevant)
  documents/                               bills (PDF) and receipt photos (PNG)
  late/                                    files that arrive AFTER the close (for the live update demo)
  answer_key.json                          the correct books (for scoring)
  README.md
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
SAMPLES = ROOT / "samples"


def money(x: D) -> str:
    return f"{x:,.2f}"


def bill_pdf(path: Path, vendor: dict, buyer: dict, number: str, day: date, lines, tax_rate: D, printed_total=None):
    subtotal = sum((a for _, a in lines), D("0"))
    tax = (subtotal * tax_rate).quantize(D("0.01"))
    total = printed_total if printed_total is not None else subtotal + tax
    c = canvas.Canvas(str(path), pagesize=A4)
    _, h = A4
    y = h - 60
    c.setFont("Helvetica-Bold", 16); c.drawString(50, y, vendor["name"]); y -= 18
    c.setFont("Helvetica", 9); c.drawString(50, y, vendor["address"]); y -= 12
    if vendor.get("gstin"):
        c.drawString(50, y, f"GSTIN: {vendor['gstin']}"); y -= 12
    y -= 10
    c.setFont("Helvetica-Bold", 13); c.drawString(50, y, "TAX INVOICE" if tax_rate else "BILL"); y -= 20
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Invoice No: {number}"); c.drawString(330, y, f"Date: {day:%d-%m-%Y}"); y -= 14
    c.drawString(50, y, f"Bill to: {buyer['name']}"); y -= 12
    c.drawString(50, y, buyer["address"]); y -= 24
    c.setFont("Helvetica-Bold", 10); c.drawString(50, y, "Description"); c.drawRightString(540, y, "Amount (INR)"); y -= 6
    c.line(50, y, 540, y); y -= 14
    c.setFont("Helvetica", 10)
    for desc, amt in lines:
        c.drawString(50, y, desc); c.drawRightString(540, y, money(amt)); y -= 14
    c.line(50, y + 4, 540, y + 4); y -= 10
    c.drawString(330, y, "Subtotal"); c.drawRightString(540, y, money(subtotal)); y -= 14
    if tax_rate:
        half = (tax / 2).quantize(D("0.01"))
        pct = tax_rate * 50
        c.drawString(330, y, f"CGST {pct:g}%"); c.drawRightString(540, y, money(half)); y -= 14
        c.drawString(330, y, f"SGST {pct:g}%"); c.drawRightString(540, y, money(tax - half)); y -= 14
    c.setFont("Helvetica-Bold", 11); c.drawString(330, y, "TOTAL"); c.drawRightString(540, y, money(total))
    c.save()


def receipt_png(path: Path, shop: str, address: str, day: date, items, messy=False):
    total = sum((a for _, a in items), D("0"))
    img = Image.new("L", (420, 120 + 26 * (len(items) + 6)), 250)
    d = ImageDraw.Draw(img)
    try:
        font, bold = ImageFont.truetype("cour.ttf", 16), ImageFont.truetype("courbd.ttf", 18)
    except OSError:
        font = bold = ImageFont.load_default()
    y = 16
    d.text((20, y), shop, font=bold, fill=10); y += 26
    d.text((20, y), address, font=font, fill=40); y += 22
    d.text((20, y), f"Date: {day:%d/%m/%Y}", font=font, fill=20); y += 30
    for name, amt in items:
        d.text((20, y), f"{name:<22}{money(amt):>12}", font=font, fill=20); y += 26
    d.text((20, y), "-" * 34, font=font, fill=60); y += 22
    d.text((20, y), f"{'TOTAL':<22}{money(total):>12}", font=bold, fill=0); y += 30
    d.text((20, y), "Thank you! Visit again", font=font, fill=60)
    if messy:
        img = img.rotate(-7, expand=True, fillcolor=235).filter(ImageFilter.GaussianBlur(1.5)).point(lambda p: 90 + p * 0.55)
    img.convert("RGB").save(path)


def write_scenario(s: dict) -> None:
    out = SAMPLES / s["slug"]
    if out.exists():
        shutil.rmtree(out)
    (out / "documents").mkdir(parents=True)
    (out / "late").mkdir()
    buyer = s["business"]
    docs_meta = {}

    def make_doc(spec, folder: Path):
        v = s["vendors"][spec["vendor"]]
        path = folder / spec["file"]
        if spec["type"] == "bill":
            bill_pdf(path, v, buyer, spec["number"], spec["date"], spec["lines"], spec.get("tax_rate", D("0.18")),
                     spec.get("printed_total"))
        else:
            receipt_png(path, v["name"].upper(), v["address"], spec["date"], spec["lines"], spec.get("messy", False))
        return path

    for t in s["transactions"]:
        if t.get("doc"):
            make_doc(t["doc"], out / "documents")
            docs_meta[t["doc"]["file"]] = {"bank_txn_id": t["id"]}
            if t["doc"].get("duplicate_as"):
                shutil.copy(out / "documents" / t["doc"]["file"], out / "documents" / t["doc"]["duplicate_as"])
                docs_meta[t["doc"]["duplicate_as"]] = {"duplicate_of": t["doc"]["file"]}

    balance = s["opening"]
    with open(out / "bank_statement.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Narration", "Ref No", "Withdrawal Amt", "Deposit Amt", "Closing Balance"])
        for t in s["transactions"]:
            balance += t["amount"]
            w.writerow([f"{t['date']:%d/%m/%y}", t["narration"], t["id"], f"{-t['amount']:.2f}" if t["amount"] < 0 else "",
                        f"{t['amount']:.2f}" if t["amount"] > 0 else "", f"{balance:.2f}"])
    closing = balance

    with open(out / "invoices_issued.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["number", "client", "date", "subtotal", "tax", "total"])
        w.writeheader()
        rate = D(s["business"]["gst_rate"])
        for inv in s.get("invoices", []):
            sub = D(inv["subtotal"]); tax = (sub * rate).quantize(D("0.01"))
            w.writerow({**inv, "tax": str(tax), "total": str(sub + tax)})
    with open(out / "timesheet.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["month", "client", "project", "hours", "billing_status"])
        w.writerows(s.get("timesheet", []))

    (out / "business.json").write_text(json.dumps(s["business"], indent=2), encoding="utf-8")
    (out / "owner_answers.json").write_text(json.dumps(s["owner_answers"], indent=2), encoding="utf-8")

    # Late arrivals: documents and/or extra bank lines that show up after the close.
    late_lines = []
    for item in s.get("late", []):
        if item["kind"] == "doc":
            make_doc(item["doc"], out / "late")
        else:
            late_lines.append(item)
    if late_lines:
        with open(out / "late" / "bank_statement_addendum.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Date", "Narration", "Ref No", "Withdrawal Amt", "Deposit Amt", "Closing Balance"])
            for t in late_lines:
                balance += t["amount"]
                w.writerow([f"{t['date']:%d/%m/%y}", t["narration"], t["id"], f"{-t['amount']:.2f}" if t["amount"] < 0 else "",
                            f"{t['amount']:.2f}" if t["amount"] > 0 else "", f"{balance:.2f}"])

    output_tax = sum((t["tax"] for t in s["transactions"] if t["account"].startswith("Income:") and t["amount"] > 0), D("0"))
    input_tax = sum((t["tax"] for t in s["transactions"] if t["amount"] < 0), D("0"))
    key = {
        "label": "GENERATED demo data: fictional business, vendors and clients",
        "scenario": s["slug"], "opening_balance": str(s["opening"]), "closing_balance": str(closing),
        "expected_tax": {"output_tax_collected": str(output_tax), "input_tax_claimable": str(input_tax),
                         "net_indirect_tax": str(output_tax - input_tax)},
        "transactions": [{"bank_txn_id": t["id"], "date": str(t["date"]), "narration": t["narration"],
                          "amount": str(t["amount"]), "account": t["account"], "tax": str(t["tax"]),
                          "documents": [t["doc"]["file"]] if t.get("doc") else [], "note": t.get("note")}
                         for t in s["transactions"]],
        "late_arrivals": [{"kind": i["kind"], "what": i.get("note")} for i in s.get("late", [])],
    }
    (out / "answer_key.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
    traps = "\n".join(f"- **{t['id']}**: {t['note']}" for t in s["transactions"] if t.get("note"))
    late = "\n".join(f"- {i.get('note')}" for i in s.get("late", []))
    (out / "README.md").write_text(
        f"# {s['business']['name']}: {s['month_label']} (GENERATED demo data)\n\n{s['about']}\n\n"
        f"Fictional business, vendors and clients. Opening balance ₹{s['opening']:,}, closing ₹{closing:,}.\n\n"
        f"## What a good accountant must catch\n{traps}\n\n## Late arrivals (`late/`): add these after the close\n{late}\n",
        encoding="utf-8")
    print(f"{s['slug']}: {len(s['transactions'])} bank lines, {len(list((out / 'documents').iterdir()))} documents, "
          f"{len(list((out / 'late').iterdir()))} late files, closing {closing}")


def T(id_, d, narration, amount, account, tax="0", doc=None, note=None):
    return {"id": id_, "date": d, "narration": narration, "amount": D(amount), "account": account, "tax": D(tax),
            "doc": doc, "note": note}


SEP = lambda day: date(2026, 9, day)  # noqa: E731

CAFE = {
    "slug": "02-filter-kaapi-house",
    "month_label": "September 2026",
    "about": "A busy 14-seat South Indian café in Mylapore, Chennai. Many small supplier bills, daily card/UPI "
             "settlements, cash for vegetables, and GST at 5% on sales without input credit.",
    "opening": D("185000.00"),
    "business": {"name": "Filter Kaapi House", "address": "12 East Mada Street, Mylapore, Chennai 600004",
                 "gstin": "33AAKFF2210B1Z7", "industry": "Café / quick-service restaurant",
                 "peer_sics": ["5812"], "hourly_rate": "0", "gst_rate": "0.05", "sales_tax_inclusive": True,
                 "input_credit_allowed": False, "income_tax_provision_rate": "0.25", "payment_terms_days": 15,
                 "non_claimable_tax_accounts": [], "client_emails": {}},
    "vendors": {
        "dairy": {"name": "Nila Dairy Farms", "address": "Red Hills Road, Chennai 600052", "gstin": "33AAGFN5521K1ZP"},
        "beans": {"name": "Chikmagalur Bean Co.", "address": "MG Road, Chikmagalur 577101", "gstin": "29AAHCC8812M1Z3"},
        "rent": {"name": "Mada Street Properties", "address": "Luz Church Road, Chennai 600004", "gstin": "33AADFM3301Q1Z9"},
        "pack": {"name": "GreenLeaf Packaging", "address": "Ambattur Industrial Estate, Chennai 600058", "gstin": "33AAJCG7741R1Z2"},
        "gas": {"name": "Sri Murugan Gas Agency", "address": "Royapettah, Chennai 600014"},
        "veg": {"name": "Koyambedu Fresh Veggies", "address": "Koyambedu Market, Chennai 600107"},
        "repair": {"name": "CoolTech Appliance Care", "address": "Adyar, Chennai 600020", "gstin": "33AAQFC1180P1Z5"},
    },
    "transactions": [
        T("C01", SEP(1), "NEFT-MADA STREET PROPERTIES-RENT SEP", "-47200.00", "Expenses:Rent", "0",
          {"type": "bill", "vendor": "rent", "file": "mada-street-rent-sep.pdf", "number": "MSP/26/09", "date": SEP(1),
           "lines": [("Shop rent - September 2026", D("40000.00"))]}),
        T("C02", SEP(2), "POS SETTLEMENT HDFC MID 88213", "38640.00", "Income:Sales", "1840.00"),
        T("C03", SEP(3), "UPI-NILA DAIRY FARMS-ND4471", "-12600.00", "Expenses:Ingredients", "0",
          {"type": "bill", "vendor": "dairy", "file": "nila-dairy-0903.pdf", "number": "ND-4471", "date": SEP(3),
           "lines": [("Toned milk 300 L", D("12000.00"))], "tax_rate": D("0.05")}),
        T("C04", SEP(4), "SAL SEP-SELVI K", "-18000.00", "Expenses:Salaries"),
        T("C05", SEP(4), "SAL SEP-RAMESH P", "-16000.00", "Expenses:Salaries"),
        T("C06", SEP(6), "UPI-CHIKMAGALUR BEAN CO-CBC921", "-14700.00", "Expenses:Ingredients", "0",
          {"type": "bill", "vendor": "beans", "file": "chikmagalur-beans-0906.pdf", "number": "CBC-921", "date": SEP(6),
           "lines": [("Peaberry roast 20 kg", D("14000.00"))], "tax_rate": D("0.05"), "duplicate_as": "WhatsApp-bill-beans.pdf"},
          "duplicate bill: the same beans bill was also forwarded on WhatsApp and uploaded twice"),
        T("C07", SEP(8), "ATM WDL MYLAPORE", "-6000.00", "Expenses:Ingredients", "0", None,
          "cash withdrawal: owner confirms it was for vegetables (petty cash)"),
        T("C08", SEP(9), "POS SETTLEMENT HDFC MID 88213", "52500.00", "Income:Sales", "2500.00"),
        T("C09", SEP(11), "UPI-GREENLEAF PACKAGING-GL331", "-8400.00", "Expenses:Packaging", "0",
          {"type": "bill", "vendor": "pack", "file": "greenleaf-packaging-0911.pdf", "number": "GL-331", "date": SEP(11),
           "lines": [("Paper cups 4000", D("5000.00")), ("Takeaway boxes 1000", D("2500.00"))], "tax_rate": D("0.12"),
           "printed_total": D("8600.00")},
          "vendor arithmetic error: 5,000 + 2,500 + 900 GST = 8,400, but the bill prints 8,600"),
        T("C10", SEP(13), "UPI-SRI MURUGAN GAS AGENCY", "-3780.00", "Expenses:Utilities", "0",
          {"type": "receipt", "vendor": "gas", "file": "gas-cylinder-receipt.png", "date": SEP(13),
           "lines": [("Commercial LPG 19kg x2", D("3780.00"))], "messy": True}, "blurry phone photo of the gas receipt"),
        T("C11", SEP(15), "TNEB-ELECTRICITY 0412 SEP", "-9850.00", "Expenses:Utilities"),
        T("C12", SEP(16), "POS SETTLEMENT HDFC MID 88213", "47250.00", "Income:Sales", "2250.00"),
        T("C13", SEP(18), "RZP*CANVA PTY LTD", "-499.00", "Expenses:Marketing", "0", None,
          "cryptic payee (Canva) with no bill: menu design subscription, not claimable without a bill"),
        T("C14", SEP(20), "IMPS-COOLTECH APPLIANCE CARE", "-5900.00", "Expenses:Repairs", "0", None,
          "fridge repair paid, bill not yet received (arrives late)"),
        T("C15", SEP(22), "RFND NILA DAIRY FARMS-SOUR BATCH", "1260.00", "Expenses:Ingredients", "0", None,
          "supplier refund for a sour milk batch: reduces ingredient cost, not income"),
        T("C16", SEP(23), "UPI-ST JOHNS SCHOOL FEES", "-22000.00", "Equity:Owner-Drawings", "0", None,
          "personal: owner's child's school fees paid from the business account"),
        T("C17", SEP(26), "POS SETTLEMENT HDFC MID 88213", "44100.00", "Income:Sales", "2100.00"),
        T("C18", SEP(30), "SMS ALERT CHGS SEP", "-59.00", "Expenses:Bank-Charges"),
    ],
    "owner_answers": {"ATM WDL": {"account": "Expenses:Ingredients", "answer": "Cash for vegetables at Koyambedu"},
                      "SCHOOL FEES": {"account": "Equity:Owner-Drawings", "answer": "Personal, my daughter's fees"}},
    "late": [
        {"kind": "doc", "note": "The CoolTech fridge-repair bill finally arrives (matches C14)",
         "doc": {"type": "bill", "vendor": "repair", "file": "cooltech-repair-bill.pdf", "number": "CT-5521", "date": SEP(20),
                 "lines": [("Compressor gas refill + service", D("5000.00"))]}},
        T("C19", SEP(30), "POS SETTLEMENT HDFC MID 88213", "21000.00", "Income:Sales", "1000.00") | {"kind": "bank",
          "note": "A late card settlement for 29-30 Sep lands on the statement"},
    ],
}

CONSULTANT = {
    "slug": "03-arjun-mehta-consulting",
    "month_label": "September 2026",
    "about": "A solo data-strategy consultant in Pune: a few large client invoices, software subscriptions, travel, "
             "and personal spending mixed into the business account.",
    "opening": D("320000.00"),
    "business": {"name": "Arjun Mehta Consulting", "address": "Baner Road, Pune 411045", "gstin": "27AAKPM8812C1ZQ",
                 "industry": "Management and data consulting", "peer_sics": ["8742"], "hourly_rate": "4500.00",
                 "gst_rate": "0.18", "income_tax_provision_rate": "0.30", "payment_terms_days": 30,
                 "non_claimable_tax_accounts": ["Expenses:Meals"],
                 "client_emails": {"Deccan Retail Pvt Ltd": "finance@deccanretail.example",
                                   "Sahyadri Agro Pvt Ltd": "accounts@sahyadriagro.example"}},
    "vendors": {
        "cowork": {"name": "Baner Hub Coworking", "address": "Baner, Pune 411045", "gstin": "27AAFCB2209H1Z1"},
        "hotel": {"name": "Hotel Sahyadri Residency", "address": "Nashik Road, Nashik 422101", "gstin": "27AAGFH5534K1Z8"},
        "cab": {"name": "Pune City Cabs", "address": "Shivajinagar, Pune 411005"},
        "acct": {"name": "Kulkarni & Associates CA", "address": "FC Road, Pune 411004", "gstin": "27AAEFK3321L1Z6"},
        "cafe": {"name": "Vohuman Cafe", "address": "Sassoon Road, Pune 411001"},
    },
    "invoices": [
        {"number": "AMC-2026-014", "client": "Deccan Retail Pvt Ltd", "date": "2026-08-05", "subtotal": "150000.00"},
        {"number": "AMC-2026-015", "client": "Sahyadri Agro Pvt Ltd", "date": "2026-08-20", "subtotal": "90000.00"},
        {"number": "AMC-2026-016", "client": "Sahyadri Agro Pvt Ltd", "date": "2026-09-02", "subtotal": "60000.00"},
        {"number": "AMC-2026-017", "client": "Deccan Retail Pvt Ltd", "date": "2026-09-10", "subtotal": "120000.00"},
    ],
    "timesheet": [("2026-09", "Sahyadri Agro Pvt Ltd", "Demand forecast model", 24, "invoiced:AMC-2026-016"),
                  ("2026-09", "Deccan Retail Pvt Ltd", "Store analytics dashboard", 18, "not invoiced")],
    "transactions": [
        T("A01", SEP(1), "NEFT-BANER HUB COWORKING-BH0926", "-17700.00", "Expenses:Rent", "2700.00",
          {"type": "bill", "vendor": "cowork", "file": "baner-hub-sep.pdf", "number": "BH-0926", "date": SEP(1),
           "lines": [("Dedicated desk - September", D("15000.00"))]}),
        T("A02", SEP(4), "NEFT CR-SAHYADRI AGRO PVT LTD-AMC015 016", "177000.00", "Income:Services", "27000.00", None,
          "one payment for two invoices (106,200 + 70,800)"),
        T("A03", SEP(5), "RZP*FIGMA INC", "-1150.00", "Expenses:Software", "0", None,
          "cryptic payee (Figma), no bill: not claimable yet"),
        T("A04", SEP(8), "UPI-PUNE CITY CABS", "-1240.00", "Expenses:Travel", "0",
          {"type": "receipt", "vendor": "cab", "file": "cab-receipt-0908.png", "date": SEP(8),
           "lines": [("Baner - Hinjewadi return", D("1240.00"))], "messy": True}, "blurry cab receipt photo"),
        T("A05", SEP(10), "UPI-HOTEL SAHYADRI RESIDENCY", "-6720.00", "Expenses:Travel", "720.00",
          {"type": "bill", "vendor": "hotel", "file": "hotel-sahyadri-0910.pdf", "number": "HSR-3381", "date": SEP(10),
           "lines": [("Room, 2 nights (client visit, Nashik)", D("6000.00"))], "tax_rate": D("0.12"),
           "duplicate_as": "hotel-invoice-email-copy.pdf"}, "duplicate: hotel invoice uploaded twice (email + download)"),
        T("A06", SEP(12), "POS VOHUMAN CAFE", "-640.00", "Expenses:Meals", "0",
          {"type": "receipt", "vendor": "cafe", "file": "vohuman-client-breakfast.png", "date": SEP(12),
           "lines": [("Client breakfast x2", D("640.00"))]}),
        T("A07", SEP(15), "NEFT-KULKARNI AND ASSOCIATES-KA77", "-11800.00", "Expenses:Professional-Fees", "1800.00",
          {"type": "bill", "vendor": "acct", "file": "kulkarni-ca-fees.pdf", "number": "KA-77", "date": SEP(15),
           "lines": [("Quarterly GST + TDS filing", D("10000.00"))], "printed_total": D("11880.00")},
          "vendor arithmetic error: 10,000 + 1,800 GST = 11,800, bill prints 11,880"),
        T("A08", SEP(18), "ONLINE SHOPPING-HEADPHONES PERSONAL", "-8999.00", "Equity:Owner-Drawings", "0", None,
          "personal purchase on the business account"),
        T("A09", SEP(22), "NEFT CR-DECCAN RETAIL PVT LTD-PART AMC014", "100000.00", "Income:Services", "15254.24", None,
          "partial payment: 100,000 of 177,000 on AMC-2026-014"),
        T("A10", SEP(25), "GST PMT CHALLAN CPIN 2609250044", "-24000.00", "Liabilities:Tax:Collected"),
        T("A11", SEP(30), "INT CR SAVINGS", "820.00", "Income:Interest"),
    ],
    "owner_answers": {"HEADPHONES": {"account": "Equity:Owner-Drawings", "answer": "Personal, for home"}},
    "late": [
        T("A12", SEP(30), "NEFT CR-DECCAN RETAIL PVT LTD-BAL AMC014", "77000.00", "Income:Services", "11745.76")
        | {"kind": "bank", "note": "Deccan Retail pays the rest of AMC-2026-014 (overdue invoice cleared)"},
    ],
}


def main() -> None:
    SAMPLES.mkdir(exist_ok=True)
    # Scenario 1: the evidence month, copied as-is, plus its late arrivals.
    src = ROOT / "data/demo/studio-kaveri/2026-09"
    out = SAMPLES / "01-studio-kaveri"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("*.page*.png", "README.md"))
    shutil.copy(ROOT / "data/answer_key/studio-kaveri-2026-09.json", out / "answer_key.json")
    (out / "late").mkdir()
    vendor = {"name": "R. Sharma Illustration", "address": "HSR Layout, Bengaluru 560102"}
    bill_pdf(out / "late" / "r-sharma-illustration-invoice.pdf", vendor,
             {"name": "Studio Kaveri Design LLP", "address": "80 Feet Road, Koramangala, Bengaluru 560034"},
             "RS-2026-09", SEP(10), [("Illustrations for Nimbus patient app (12 screens)", D("12000.00"))], D("0"))
    with open(out / "late" / "bank_statement_addendum.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Narration", "Ref No", "Withdrawal Amt", "Deposit Amt", "Closing Balance"])
        w.writerow(["30/09/26", "NEFT CR-ORBIT LOGISTICS PVT LTD-INV KAV-2026-029", "B22", "", "141600.00", "868335.18"])
    (out / "README.md").write_text(
        "# Studio Kaveri Design LLP: September 2026 (GENERATED demo data)\n\nA 6-person design and digital studio in "
        "Bengaluru. Client invoices, software, rent, salaries, a late-paying client and un-invoiced work.\n\n"
        "12 planted traps: see `answer_key.json`.\n\n## Late arrivals (`late/`)\n"
        "- R. Sharma's invoice for the illustration payment (B11): the contractor payment gets its bill\n"
        "- Orbit Logistics finally pays the overdue invoice KAV-2026-029 (₹1,41,600)\n", encoding="utf-8")
    print("01-studio-kaveri: copied evidence month + late arrivals")
    for s in (CAFE, CONSULTANT):
        write_scenario(s)


if __name__ == "__main__":
    main()
