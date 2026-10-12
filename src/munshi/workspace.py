"""A business's working folder: start from a sample (or uploads) and add files as they arrive."""

import json
import shutil
from datetime import datetime
from pathlib import Path

from munshi.config import ROOT

SAMPLES = ROOT / "samples"
WORK = ROOT / "runs" / "workspace"
DOC_TYPES = {".pdf", ".png", ".jpg", ".jpeg"}


def scenarios() -> list[dict]:
    out = []
    for d in sorted(p for p in SAMPLES.iterdir() if p.is_dir()):
        biz = json.loads((d / "business.json").read_text(encoding="utf-8"))
        out.append({"slug": d.name, "name": biz["name"], "industry": biz.get("industry", ""),
                    "late": sorted(p.name for p in (d / "late").iterdir()) if (d / "late").exists() else []})
    return out


def start_from_sample(slug: str) -> Path:
    """Fresh copy of a sample's month (without its late arrivals or answer key)."""
    dest = WORK / slug
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SAMPLES / slug, dest, ignore=shutil.ignore_patterns("late", "answer_key.json", "README.md", "*.page*.png"))
    return dest


def add_file(workspace: Path, name: str, data: bytes) -> str:
    """Put an arriving file where it belongs. Returns what it was filed as."""
    suffix = Path(name).suffix.lower()
    if suffix in DOC_TYPES:
        (workspace / "documents" / Path(name).name).write_bytes(data)
        return "document"
    if suffix == ".csv":
        header = data.decode("utf-8", errors="replace").splitlines()[0].lower()
        if "narration" in header and "balance" in header:
            stamp = datetime.now().strftime("%H%M%S%f")
            (workspace / f"bank_statement_addendum_{stamp}.csv").write_bytes(data)
            return "bank lines"
        if "client" in header and "total" in header:
            (workspace / "invoices_issued.csv").write_bytes(data)
            return "invoices sent"
        if "hours" in header:
            (workspace / "timesheet.csv").write_bytes(data)
            return "timesheet"
    raise ValueError(f"Don't know what {name} is (bank CSV, invoices CSV, timesheet CSV, or a bill/receipt PDF/image)")


def add_late_arrivals(workspace: Path, slug: str) -> list[str]:
    added = []
    late = SAMPLES / slug / "late"
    for p in sorted(late.iterdir()) if late.exists() else []:
        added.append(f"{p.name} → {add_file(workspace, p.name, p.read_bytes())}")
    return added


def forget(ws: Path) -> None:
    """Start a business fresh: drop Munshi's memory of it and of its documents, so the first close is real work."""
    import hashlib
    import re
    biz = json.loads((ws / "business.json").read_text(encoding="utf-8"))
    mem = ROOT / "state" / "memory" / (re.sub(r"\W+", "-", biz["name"].lower()).strip("-") + ".json")
    mem.unlink(missing_ok=True)
    reads = ROOT / "state" / "reads"
    for d in (ws / "documents").iterdir():
        (reads / f"{hashlib.sha256(d.read_bytes()).hexdigest()[:16]}.json").unlink(missing_ok=True)
    late = SAMPLES / ws.name / "late"
    for d in late.iterdir() if late.exists() else []:
        (reads / f"{hashlib.sha256(d.read_bytes()).hexdigest()[:16]}.json").unlink(missing_ok=True)


def new_business(name: str, industry: str, city: str, gst_rate: str, input_credit: bool) -> Path:
    """An empty month for your own business: add a bank statement and bills, then close it."""
    import re
    slug = "custom-" + re.sub(r"\W+", "-", name.lower()).strip("-")
    dest = WORK / slug
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "documents").mkdir(parents=True)
    (dest / "business.json").write_text(json.dumps({
        "name": name, "address": city, "industry": industry, "peer_sics": ["8742"], "hourly_rate": "0",
        "gst_rate": gst_rate, "income_tax_provision_rate": "0.25", "payment_terms_days": 15,
        "input_credit_allowed": input_credit, "non_claimable_tax_accounts": ["Expenses:Meals"], "client_emails": {},
    }, indent=2), encoding="utf-8")
    (dest / "owner_answers.json").write_text("{}", encoding="utf-8")
    return dest
