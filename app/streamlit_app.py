"""Munshi: an AI CA that closes a messy month of books, recovers when they don't balance, and proves every number.

Three pages: 1 · Your month (give Munshi your files)  2 · The office (the team at work)  3 · Books & proof.
"""

import base64
import csv
import hashlib
import json
import re
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import ui  # noqa: E402
from munshi import close, tracing, workspace  # noqa: E402
from munshi.config import settings  # noqa: E402

EVIDENCE = ROOT / "evidence/runs"
READ_ONLY = not settings.llm_api_key
THUMBS = ROOT / "state" / "thumbs"

st.set_page_config(page_title="Munshi · your AI CA", page_icon="🧾", layout="wide")
st.html(ui.CSS)
st.html(ui.OFFICE_CSS)
S = st.session_state


# --------------------------------------------------------------------------- state & data

@st.cache_resource
def _tracing() -> bool:
    return tracing.init("v3-app")


def current_workspace() -> Path:
    if "ws" not in S:
        S["slug"] = "01-studio-kaveri"
        S["ws"] = str(workspace.start_from_sample(S["slug"]))
        workspace.forget(Path(S["ws"]))
    return Path(S["ws"])


def choose(slug: str) -> None:
    S.update(slug=slug, ws=str(workspace.start_from_sample(slug)), run_dir=None, chat=[], decided={},
             links={}, bubbles={}, states={}, new_files=[])
    workspace.forget(Path(S["ws"]))


def run_data() -> dict | None:
    r = S.get("run_dir")
    if not r and READ_ONLY and S.get("slug", "01-studio-kaveri") == "01-studio-kaveri":
        r = str(EVIDENCE / "close-v2")
    if not r or not (Path(r) / "facts.json").exists():
        return None
    j = lambda n: json.loads((Path(r) / n).read_text(encoding="utf-8"))
    return {"facts": j("facts.json"), "entries": j("entries.json"), "actions": j("actions.json"), "dir": Path(r)}


def business(ws: Path) -> dict:
    return json.loads((ws / "business.json").read_text(encoding="utf-8"))


def thumb(path: Path) -> str | None:
    """Small preview image (PDF first page or the photo itself) as a data URI."""
    THUMBS.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    out = THUMBS / f"{key}.png"
    if not out.exists():
        try:
            if path.suffix.lower() == ".pdf":
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    pdf.pages[0].to_image(resolution=40).save(out)
            else:
                from PIL import Image
                im = Image.open(path)
                im.thumbnail((300, 300))
                im.save(out)
        except Exception:
            return None
    return "data:image/png;base64," + base64.b64encode(out.read_bytes()).decode()


def inventory(ws: Path) -> dict:
    docs = sorted(p for p in (ws / "documents").iterdir()
                  if p.suffix.lower() in workspace.DOC_TYPES and ".page" not in p.name)
    bank = close.load_bank(ws)
    invoices, hours = [], 0
    if (ws / "invoices_issued.csv").exists():
        with open(ws / "invoices_issued.csv", encoding="utf-8") as f:
            invoices = list(csv.DictReader(f))
    if (ws / "timesheet.csv").exists():
        with open(ws / "timesheet.csv", encoding="utf-8") as f:
            hours = sum(int(r["hours"] or 0) for r in csv.DictReader(f))
    return {"docs": docs, "bills": [d for d in docs if d.suffix.lower() == ".pdf"],
            "photos": [d for d in docs if d.suffix.lower() != ".pdf"], "bank": bank, "invoices": invoices, "hours": hours}


STEP_TO_WORKER = {step: key for key, *_, steps in ui.TEAM for step in steps}


def short(msg: str) -> str:
    msg = re.sub(r"\s+", " ", msg)
    return msg if len(msg) <= 60 else msg[:57] + "…"


def _acct(text: str) -> str:
    return re.sub(r"(Expenses|Income|Liabilities|Equity|Assets):", "", text).replace("Tax:Collected", "GST").replace("-", " ")


def friendly(step: str, msg: str) -> str:
    """What the worker would say out loud."""
    remembered = "(remembered)" in msg
    msg = msg.replace(" (remembered)", "")
    m = re.match(r".*?(\d+) peers; median operating margin ([\d.]+%)", msg)
    if step == "research" and m:
        return f"Found {m.group(1)} real peers · median margin {m.group(2)}"
    if step == "research":
        return "Looking up real peers (SEC filings)"
    if step == "read":
        m = re.match(r"(.+?): (.+?) ₹([\d.,]+)(.*)", msg)
        if m:
            flag = " ⚠ total doesn't add up" if "vendor error" in m.group(4) else ""
            verb = "Already read" if remembered else "Read"
            return f"{verb} {m.group(2)[:24]} · ₹{m.group(3)}{flag}"
    if step == "match" and "duplicate" in msg:
        return "Spotted a duplicate upload"
    if step == "post":
        m = re.match(r"(\S+) (.+?) → (\S+)", msg)
        if m:
            return f"{m.group(2)[:22].title()} → {_acct(m.group(3))}" + (" ✓" if remembered else "")
        return _acct(msg)
    if step == "verify":
        m = re.search(r"gap ₹(-?[\d.]+)", msg)
        return f"Books off by ₹{abs(float(m.group(1))):,.0f}, hunting…" if m and "✗" in msg else "Books match the bank ✓"
    if step == "gap_hunt":
        return "Found it: duplicate bill" if "duplicate" in msg else ("Found it: vendor's total is wrong"
                                                                      if "vendor" in msg else "Found the gap")
    if step == "actions":
        if msg.startswith("Un-invoiced"):
            return "Drafted an invoice for un-billed work"
        if "overdue" in msg:
            return "Drafted a payment reminder"
        if "no bill" in msg:
            return "A bill is missing: request drafted"
    if step == "brief":
        return "Your brief is ready"
    return msg


# --------------------------------------------------------------------------- the close (live + incremental)

def run_close(office_box, feed_box, previous: dict | None = None) -> None:
    ws = current_workspace()
    states = {k: "idle" for k, *_ in ui.TEAM}
    bubbles: dict[str, tuple[str, str]] = {}
    feed: list[str] = []

    def progress(step, message, data=None):
        worker = STEP_TO_WORKER.get(step)
        if worker:
            for k, *_ in ui.TEAM:
                if k == worker:
                    break
                if states[k] == "working":
                    states[k] = "done"
            states[worker] = "working"
            style = "warn" if ("✗" in message or "⚠" in message or step == "gap_hunt") else ("ok" if "✅" in message else "")
            bubbles[worker] = (short(friendly(step, message)), style)
        feed.append(f"<div><b>{step}</b> · {message}</div>")
        office_box.html(ui.office(states, bubbles))
        feed_box.html('<div class="card" style="font-size:13px;line-height:1.7;max-height:200px;overflow:hidden">'
                      + "".join(feed[-7:]) + "</div>")

    _tracing()
    out = ROOT / "runs" / f"app-{datetime.now():%Y%m%d-%H%M%S}-{S['slug']}"
    with tracing.run("munshi-close-app", session_id=f"office-{S['slug']}", end_user_id=S["slug"]):
        close.close_v2(ws, out, progress=progress, previous=previous)
    for k, *_ in ui.TEAM:
        if states[k] == "working" or previous is None:
            states[k] = "done"
    S.update(run_dir=str(out), states=states, bubbles=bubbles)
    feed_box.empty()


# --------------------------------------------------------------------------- page 1: your month

def month_page():
    ws = current_workspace()
    left, right = st.columns([1, 3], gap="large")
    with left:
        st.html('<div class="title" style="font-size:24px">Pick a business</div>')
        for sc in workspace.scenarios():
            active = sc["slug"] == S.get("slug")
            if st.button(sc["name"], key=f"pick-{sc['slug']}", width="stretch",
                         type="primary" if active else "secondary", help=sc["industry"]):
                choose(sc["slug"])
                st.rerun()
        st.html('<div class="muted" style="font-size:13px;margin:16px 0 6px">Or add your own files to this month</div>')
        files = st.file_uploader("Bank CSV · bills (PDF) · receipt photos · invoices / timesheet CSV",
                                 accept_multiple_files=True, disabled=READ_ONLY, key=f"up-{S.get('slug')}",
                                 label_visibility="collapsed")
        if files and st.button("Add these files", width="stretch", disabled=READ_ONLY, key="add-files"):
            for f in files:
                try:
                    kind = workspace.add_file(ws, f.name, f.getvalue())
                    S.setdefault("new_files", []).append(f.name)
                    st.toast(f"{f.name} → {kind}")
                except ValueError as e:
                    st.error(str(e))
            st.rerun()
    with right:
        biz = business(ws)
        inv = inventory(ws)
        head = st.columns([2, 1])
        head[0].html(f'<div class="title">What you gave Munshi</div>'
                     f'<p class="sub" style="margin:0">{biz["name"]} · {biz.get("industry", "")} · September 2026</p>')
        with head[1]:
            st.html('<div style="height:16px"></div>')
            if st.button("Hand it to the team →", type="primary", width="stretch", key="handover"):
                S["autostart"] = not READ_ONLY and not S.get("run_dir")
                st.switch_page(PAGES["office"])
        cats = st.columns(5)
        for col, args in zip(cats, [("bank", str(len(inv["bank"])), "bank lines"),
                                    ("bill", str(len(inv["bills"])), "bills"),
                                    ("photo", str(len(inv["photos"])), "receipt photos"),
                                    ("invoice", str(len(inv["invoices"])), "invoices sent"),
                                    ("clock", f"{inv['hours']} h", "timesheet")]):
            col.html(ui.category(*args))
        st.html('<div style="height:8px"></div>')
        grid = st.columns(4)
        new = set(S.get("new_files", []))
        for i, d in enumerate(inv["docs"]):
            kind = "Bill · PDF" if d.suffix.lower() == ".pdf" else "Receipt · photo"
            grid[i % 4].html(ui.doc_card(d.name, kind, thumb(d), new=d.name in new))
        with st.expander(f"Bank statement · {len(inv['bank'])} lines"):
            st.dataframe([{"Date": t.date.strftime("%d %b"), "Narration": t.description, "Amount ₹": float(t.amount)}
                          for t in inv["bank"]], hide_index=True, width="stretch")
        if inv["invoices"]:
            with st.expander(f"Invoices you sent · {len(inv['invoices'])}"):
                st.dataframe(inv["invoices"], hide_index=True, width="stretch")
        st.html(ui.note("Sample businesses are generated demo data (see samples/). "
                        "The reader is benchmarked on real receipts.", logo=None))


# --------------------------------------------------------------------------- page 2: the office

def office_page():
    ws = current_workspace()
    biz = business(ws)
    d = run_data()
    left, right = st.columns([2, 1], gap="large")
    with left:
        said = "Thanks, team! 🙏" if d and d["facts"]["balanced"] else "Close September for me, please."
        st.html(ui.owner(f"{said} <span class='muted' style='font-size:13px'> · Kavya, owner of {biz['name']}</span>"))
        office_box, feed_box = st.empty(), st.empty()
        states = S.get("states") or ({k: "done" for k, *_ in ui.TEAM} if d else {})
        bubbles = S.get("bubbles") or ({} if not d else {"auditor": ("Books match the bank: ₹0", "ok")})
        office_box.html(ui.office(states, bubbles))
        if READ_ONLY:
            st.info("Read-only demo: showing the recorded close. Run locally with API keys to watch the team work live.")
        elif not d:
            if st.button("Start the close", type="primary", width="stretch", key="start") or S.pop("autostart", False):
                run_close(office_box, feed_box)
                st.rerun()
    with right:
        if not d:
            st.html('<div class="status wait"><div><div class="t">Ready when you are</div>'
                    '<div class="muted" style="font-size:13px">The team hasn\'t started yet.</div></div></div>')
            return
        f, a = d["facts"], d["actions"]
        t = f["tax"]
        ok = f["balanced"]
        st.html(f'<div class="status {"ok" if ok else "wait"}"><div><div class="t">'
                f'{"September closed ✓" if ok else "Not closed yet"}</div><div style="font-size:13px;font-weight:600">'
                f'{"Books match the bank: ₹0" if ok else "Books are off by " + ui.inr(f["bank_gap"])}</div></div></div>')
        owed = sum(Decimal(i["open"]) for i in f.get("open_invoices", []))
        m = st.columns(3)
        for col, (lab, val) in zip(m, [("Profit", t["profit"]), ("Tax aside", t["set_aside"]), ("Owed to you", owed)]):
            col.html(f'<div class="mini"><div class="l">{lab}</div><div class="v">{ui.inr(val)}</div></div>')
        if f.get("gap_hunt"):
            names = {"duplicate_post": "duplicate bill removed", "amount_mismatch": "vendor's wrong total caught"}
            st.html('<div class="changed" style="background:#1A2621"><div class="h" style="color:#8FE3B5">'
                    'Fixed during the close</div>'
                    + "".join(f"<div>{ui.inr(abs(Decimal(h['effect'])))} · {names.get(h['kind'], h['kind'])}</div>"
                              for h in f["gap_hunt"]) + "</div>")
        if f.get("changes"):
            st.html('<div class="changed"><div class="h">What changed</div>'
                    + "".join(f"<div>{c}</div>" for c in f["changes"]) + "</div>")
        approvals(a)
        with st.container(border=True):
            st.markdown("**Something new arrived?**  \nDrop a bill or bank lines; only the affected workers react.")
            new_files = st.file_uploader("new", accept_multiple_files=True, label_visibility="collapsed",
                                         disabled=READ_ONLY, key=f"late-{S.get('slug')}-{S.get('run_dir')}")
            c = st.columns(2)
            go_new = c[0].button("Add & update", width="stretch", disabled=READ_ONLY or not new_files, key="add-new")
            go_late = c[1].button("Late files", width="stretch", disabled=READ_ONLY, key="add-late",
                                  help="Adds this sample's late arrivals (samples/<business>/late)")
        if go_new or go_late:
            previous = {"entries": d["entries"], "facts": f, "actions": a}
            if go_late:
                added = workspace.add_late_arrivals(ws, S["slug"])
                S.setdefault("new_files", []).extend(x.split(" →")[0] for x in added)
            else:
                for nf in new_files:
                    workspace.add_file(ws, nf.name, nf.getvalue())
                    S.setdefault("new_files", []).append(nf.name)
            with left:
                run_close(office_box, feed_box, previous=previous)
            st.rerun()
        chat_box(d)


def approvals(a: dict) -> None:
    decided, links = S.setdefault("decided", {}), S.setdefault("links", {})
    items = ([("invoice", i, f"🧾 Invoice {i['client'].split()[0]} {ui.inr(i['total'])}") for i in a["invoices"]]
             + [("reminder", r, f"⏰ Remind {r['client'].split()[0]} {ui.inr(r['open'])}") for r in a["reminders"]]
             + [("bill", m, f"📎 Bill from {m['payee'].split('-')[-1].split('*')[-1][:14].title()} {ui.inr(m['amount'])}")
                for m in a["missing_bills"]])
    if not items:
        return
    with st.container(border=True):
        st.markdown(f"**{len(items)} drafts need your OK**")
        for kind, item, label in items:
            key = f"{kind}-{label}"
            c = st.columns([3, 2])
            c[0].markdown(f"{'✅ ' if decided.get(key) == 'approved' else ''}{label}")
            if decided.get(key) != "approved":
                if c[1].button("Approve", key=f"ok-{key}", type="primary", width="stretch", disabled=READ_ONLY):
                    decided[key] = "approved"
                    if kind == "invoice":
                        link = (item.get("dodo") or {}).get("checkout_url")
                        if not link:
                            from munshi.integrations import dodo
                            biz = business(current_workspace())
                            with st.spinner("Creating Dodo payment link…"):
                                link = dodo.payment_link(item["number"], f"{item['project']} ({item['hours']} h)",
                                                         Decimal(item["total"]), item["client"],
                                                         biz.get("client_emails", {}).get(item["client"],
                                                                                          "accounts@example.com"))["checkout_url"]
                        links[key] = link
                    st.rerun()
            elif kind == "invoice" and links.get(key):
                c[1].link_button("Pay link", links[key], width="stretch")


def chat_box(d: dict) -> None:
    history = S.setdefault("chat", [])
    with st.container(border=True):
        st.markdown("**Ask Munshi**")
        for h in history[-3:]:
            st.chat_message("user").write(h["q"])
            st.chat_message("assistant", avatar="🧾").write(h["a"])
        q = None
        cols = st.columns(2)
        if cols[0].button("Who owes me money?", width="stretch", disabled=READ_ONLY, key="q1"):
            q = "Who owes me money?"
        if cols[1].button("How much can I spend?", width="stretch", disabled=READ_ONLY, key="q2"):
            q = "After setting aside tax, how much can I safely spend this month?"
        typed = st.text_input("Ask about your books", key="ask", label_visibility="collapsed",
                              placeholder="Ask about your books…", disabled=READ_ONLY)
        if st.button("Ask", width="stretch", disabled=READ_ONLY or not typed, key="ask-btn"):
            q = typed
        if q:
            from munshi import chat
            _tracing()
            with st.spinner("Checking the books…"):
                history.append({"q": q, "a": chat.answer(q, d["dir"], history)})
            st.rerun()


# --------------------------------------------------------------------------- page 3: books & proof

def _decided(e: dict) -> tuple[str, str]:
    d = e["decided_by"]
    if d.startswith("rule:refund"):
        return "Refund rule", "bookkeeper"
    if d.startswith("rule:"):
        return "Rule", "bookkeeper"
    if d == "owner":
        return "You", "owner"
    if d.startswith("match:"):
        n = len(e["document_ids"])
        return f"{n} invoice{'s' if n > 1 else ''}", "bookkeeper"
    if "crustdata" in d:
        return "Crustdata", "bookkeeper"
    return ("Bill", "reader") if e["document_ids"] else ("AI", "bookkeeper")


def _account(a: str) -> str:
    return {"Liabilities:Tax:Collected": "GST paid", "Equity:Owner-Drawings": "Personal"}.get(
        a, a.split(":")[-1].replace("-", " "))


def books_page():
    d = run_data()
    if not d:
        st.info("Close the month in the office first.")
        return
    s1 = json.loads((EVIDENCE / "close-v1/score.json").read_text())
    s2 = json.loads((EVIDENCE / "close-v2/score.json").read_text())
    from munshi import benchmark
    b1 = benchmark.rescore(sorted((EVIDENCE / "benchmark").glob("benchmark-v1-*.json"))[-1])["accuracy"]
    b2 = benchmark.rescore(EVIDENCE / "benchmark/benchmark-v2-after-fix.json")["accuracy"]
    p = st.columns(4)
    p[0].html(f'<div class="tile green"><div class="label">Books vs bank</div><div class="big">₹0 off</div>'
              f'<div style="font-size:12px">naive v1 was {ui.inr(abs(Decimal(s1["bank_gap"])))} off</div></div>')
    p[1].html(f'<div class="tile"><div class="label">Traps caught</div><div class="big">{s2["traps_caught"]}/{s2["traps_total"]}</div>'
              f'<div class="muted" style="font-size:12px">naive v1 caught {s1["traps_caught"]}</div></div>')
    p[2].html(f'<div class="tile"><div class="label">Real receipts: vendor read</div><div class="big">{b2["company"]:.0%}</div>'
              f'<div class="muted" style="font-size:12px">v1 {b1["company"]:.1%} · 40 SROIE receipts</div></div>')
    p[3].html(f'<div class="tile"><div class="label">Traced &amp; versioned</div>'
              f'<div style="display:flex;gap:12px;align-items:center;margin-top:14px">'
              f'<img src="{ui.LOGO["neatlogs"]}" style="width:30px;height:30px;border-radius:8px" alt="neatlogs">'
              f'<img src="{ui.LOGO["entire"]}" style="height:15px" alt="Entire"></div>'
              f'<div class="muted" style="font-size:12px;margin-top:10px">'
              f'−{(1 - s2["llm_tokens"] / s1["llm_tokens"]) * 100:.0f}% tokens per close</div></div>')
    st.caption("Proof tiles come from the recorded evidence run (Studio Kaveri, neatHack models). "
               "The table below is the business you closed.")
    entries = sorted(d["entries"], key=lambda e: (e["date"], e["bank_txn_id"]))
    rows = [{"Date": datetime.strptime(e["date"], "%Y-%m-%d").strftime("%d %b"), "Payee": e["payee"][:30],
             "Account": _account(e["account"]), "Amount ₹": float(e["amount"]), "Decided by": _decided(e)[0]}
            for e in entries]
    left, right = st.columns([5, 3], gap="large")
    with left:
        st.html('<div class="title" style="font-size:28px">Every entry has a reason</div>')
        sel = st.dataframe(rows, hide_index=True, width="stretch", height=520, on_select="rerun",
                           selection_mode="single-row", key="books-table",
                           column_config={"Amount ₹": st.column_config.NumberColumn(format="%,.0f")})
    chosen = sel.selection.rows if sel and getattr(sel, "selection", None) else []
    i = chosen[0] if chosen else next((k for k, e in enumerate(entries) if "crustdata" in e["decided_by"]), 0)
    e = entries[i]
    label, who = _decided(e)
    acct = _account(e["account"])
    steps = {"Rule": ["Bank line matched a standard pattern", f"Booked as {acct}"],
             "You": ["Munshi wasn't sure, so it asked you", f"You said: {e['narration']}", f"Booked as {acct}"],
             "Bill": [f"Matched to {', '.join(e['document_ids'])}", "Totals re-added in code", f"Booked as {acct}"],
             "Crustdata": ["Cryptic bank line", f"Looked up: {e['narration'].split(':')[0]}", f"Booked as {acct}"],
             "Refund rule": ["Money came back from a vendor", "Linked to the original payment", "Reduces that expense"]
             }.get(label, [e["narration"][:110], f"Booked as {acct}"])
    names = {"bookkeeper": "Meena, the Bookkeeper", "reader": "Arjun, the Reader", "owner": "you (Kavya)"}
    warn = ""
    if e["amount"].startswith("-") and not e["document_ids"] and e["account"].startswith("Expenses") \
            and not e["decided_by"].startswith(("rule", "owner")):
        warn = '<div class="warn">No bill yet, so tax can\'t be claimed. Request drafted.</div>'
    if "vendor bill total" in e["narration"]:
        warn = '<div class="warn">Vendor\'s bill total was wrong; the bank figure was booked.</div>'
    with right:
        st.html('<div style="height:52px"></div>')
        st.html(f'<div class="why"><div class="k">WHY THIS ENTRY</div><div class="h">{e["payee"][:30]} → {acct}</div>'
                f'<div class="mono" style="font-size:22px;margin-bottom:10px">{ui.inr(e["amount"], sign=True)}</div>'
                + "".join(f'<div class="step"><span class="n">{k}</span><span>{s}</span></div>'
                          for k, s in enumerate(steps, 1))
                + warn + f'<div style="display:flex;align-items:center;gap:10px;margin-top:14px">'
                f'<img src="{ui.AVATAR[who]}" style="width:44px;height:44px" alt="">'
                f'<span style="font-size:13px;color:#3E4A44">Decided by {names[who]}</span></div></div>')


PAGES = {
    "month": st.Page(month_page, title="1 · Your month", default=True, url_path="month"),
    "office": st.Page(office_page, title="2 · The office", url_path="office"),
    "books": st.Page(books_page, title="3 · Books & proof", url_path="books"),
}
if __name__ == "__main__" or __name__ == "__page__":
    st.navigation(list(PAGES.values()), position="top").run()
