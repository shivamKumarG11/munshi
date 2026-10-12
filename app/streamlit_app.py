"""Munshi: an AI CA that closes a messy month of books, recovers when they don't balance, and proves every number.

Three pages: 1 · Your month (give Munshi your files)  2 · The office (the team at work)  3 · Books & proof.
"""

import base64
import csv
import os
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

try:  # Streamlit Cloud: secrets -> environment, before munshi.config reads it
    for _k, _v in st.secrets.items():
        if isinstance(_v, (str, int, float, bool)):
            os.environ.setdefault(_k, str(_v))
except Exception:  # no secrets file locally: .env is used instead
    pass

import ui  # noqa: E402
from munshi import close, tracing, workspace  # noqa: E402
from munshi.config import settings  # noqa: E402

EVIDENCE = ROOT / "evidence/runs"
READ_ONLY = not settings.llm_api_key
PUBLIC = os.environ.get("MUNSHI_PUBLIC_DEMO", "").lower() in ("1", "true", "yes")
LIMITS = {"closes": 3, "questions": 10}   # per visitor, only on the public demo


def allowed(kind: str) -> bool:
    """Public demo guard rail: each visitor gets a few live closes and questions."""
    if not PUBLIC:
        return True
    used = S.setdefault("used", {"closes": 0, "questions": 0})
    if used[kind] >= LIMITS[kind]:
        st.warning(f"Demo limit reached ({LIMITS[kind]} {kind} per visitor). Run it locally for unlimited use.")
        return False
    used[kind] += 1
    return True


def recorded_bubbles() -> dict:
    """What each worker said last in the recorded evidence close (for the read-only demo)."""
    log = EVIDENCE / "close-v2" / "close.log"
    bubbles = {}
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            m = re.match(r"\[(\w+)\] (.*)", line)
            if m and STEP_TO_WORKER.get(m.group(1)):
                style = "warn" if ("✗" in m.group(2) or m.group(1) == "gap_hunt") else ("ok" if "✅" in m.group(2) else "")
                bubbles[STEP_TO_WORKER[m.group(1)]] = (short(friendly(m.group(1), m.group(2))), style)
    return bubbles
THUMBS = ROOT / "state" / "thumbs"

st.set_page_config(page_title="Munshi · your AI CA", page_icon="🧾", layout="wide")
st.html(ui.CSS)
st.html(ui.OFFICE_CSS)
st.html(ui.LINE_CSS)
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

def run_close(office_box, feed_box, previous: dict | None = None, owner_says: str = "Close September, please") -> None:
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
        who = {k: f"{n}" for k, n, *_ in ui.TEAM}.get(worker, "Munshi")
        feed.append(f"<div><b>{who}</b> · {friendly(step, message)}</div>")
        office_box.html(ui.line(states, bubbles, owner_says))
        feed_box.html('<div class="card" style="font-size:13px;line-height:1.7;max-height:200px;overflow:hidden">'
                      + "".join(feed[-7:]) + "</div>")

    _tracing()
    out = ROOT / "runs" / f"app-{datetime.now():%Y%m%d-%H%M%S}-{S['slug']}"
    try:
        with tracing.run("munshi-close-app", session_id=f"office-{S['slug']}", end_user_id=S["slug"]):
            close.close_v2(ws, out, progress=progress, previous=previous)
    except Exception as e:  # show it, never fail silently
        feed_box.empty()
        st.error(f"The close stopped: {type(e).__name__}: {e}")
        st.stop()
    for k, *_ in ui.TEAM:
        if states[k] == "working" or previous is None:
            states[k] = "done"
    S.update(run_dir=str(out), states=states, bubbles=bubbles)
    feed_box.empty()


# --------------------------------------------------------------------------- page 1: your month

@st.dialog("Document", width="large")
def view_document(path_str: str) -> None:
    path = Path(path_str)
    st.caption(path.name)
    if path.suffix.lower() == ".pdf":
        import pdfplumber
        big = THUMBS / f"big-{hashlib.sha256(path.read_bytes()).hexdigest()[:16]}.png"
        if not big.exists():
            with pdfplumber.open(path) as pdf:
                pdf.pages[0].to_image(resolution=110).save(big)
        st.image(str(big), width="stretch")
    else:
        st.image(str(path), width="stretch")


def business_picker(ws: Path) -> None:
    biz = business(ws)
    with st.popover(f"🏢  {biz['name']}  ▾", width="stretch"):
        st.markdown("**Sample businesses**")
        for sc in workspace.scenarios():
            if st.button(f"{sc['name']}  ·  {sc['industry']}", key=f"pick-{sc['slug']}", width="stretch",
                         type="primary" if sc["slug"] == S.get("slug") else "secondary"):
                choose(sc["slug"])
                st.rerun()
        st.divider()
        st.markdown("**+ New business**")
        with st.form("new-biz", border=False):
            name = st.text_input("Business name", placeholder="e.g. Sharma Electricals")
            industry = st.text_input("What it does", placeholder="e.g. Electrical contractor")
            city = st.text_input("City", placeholder="e.g. Jaipur")
            c = st.columns(2)
            gst = c[0].selectbox("GST rate on sales", ["0.18", "0.12", "0.05", "0"], index=0)
            credit = c[1].checkbox("Claims input tax credit", value=True)
            if st.form_submit_button("Create business", type="primary", width="stretch", disabled=READ_ONLY):
                if not name.strip():
                    st.error("Give the business a name.")
                else:
                    ws_new = workspace.new_business(name.strip(), industry.strip() or "Small business",
                                                    city.strip(), gst, credit)
                    S.update(slug=ws_new.name, ws=str(ws_new), run_dir=None, chat=[], decided={}, links={},
                             bubbles={}, states={}, new_files=[])
                    st.rerun()


def month_page():
    ws = current_workspace()
    biz = business(ws)
    inv = inventory(ws)
    head = st.columns([2, 1.2, 1])
    head[0].html(f'<div class="title">What you gave Munshi</div>'
                 f'<p class="sub" style="margin:0">{biz.get("industry", "")} · September 2026</p>')
    with head[1]:
        st.html('<div style="height:18px"></div>')
        business_picker(ws)
    with head[2]:
        st.html('<div style="height:18px"></div>')
        if st.button("Hand it to the team →", type="primary", width="stretch", key="handover",
                     disabled=not inv["bank"]):
            S["autostart"] = not READ_ONLY and not S.get("run_dir")
            st.switch_page(PAGES["office"])
    cats = st.columns(5)
    for col, args in zip(cats, [("bank", str(len(inv["bank"])), "bank lines"),
                                ("bill", str(len(inv["bills"])), "bills"),
                                ("photo", str(len(inv["photos"])), "receipt photos"),
                                ("invoice", str(len(inv["invoices"])), "invoices sent"),
                                ("clock", f"{inv['hours']} h", "timesheet")]):
        col.html(ui.category(*args))
    with st.expander("➕  Add files to this month (bank CSV · bills · receipt photos · invoices / timesheet CSV)",
                     expanded=not inv["bank"]):
        files = st.file_uploader("files", accept_multiple_files=True, disabled=READ_ONLY,
                                 key=f"up-{S.get('slug')}", label_visibility="collapsed")
        if files and st.button("Add these files", type="primary", disabled=READ_ONLY, key="add-files"):
            for f in files:
                try:
                    kind = workspace.add_file(ws, f.name, f.getvalue())
                    S.setdefault("new_files", []).append(f.name)
                    st.toast(f"{f.name} → {kind}")
                except ValueError as e:
                    st.error(str(e))
            st.rerun()
    if not inv["bank"]:
        st.info("Add a bank statement CSV to start (columns: Date, Narration, Ref No, Withdrawal Amt, "
                "Deposit Amt, Closing Balance). See samples/ for examples.")
    st.html('<div style="height:6px"></div>')
    grid = st.columns(4)
    new = set(S.get("new_files", []))
    for i, d in enumerate(inv["docs"]):
        kind = "Bill · PDF" if d.suffix.lower() == ".pdf" else "Receipt · photo"
        with grid[i % 4]:
            st.html(ui.doc_card(d.name, kind, thumb(d), new=d.name in new))
            if st.button("View large", key=f"view-{d.name}", width="stretch"):
                view_document(str(d))
    if inv["bank"]:
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
    title_box = st.empty()
    controls = st.columns([3, 1.3, 1])
    with controls[1]:
        add_new = None
        with st.popover("+ Something new arrived", width="stretch", disabled=READ_ONLY or not d):
            st.markdown("Drop a bill or bank lines. Munshi remembers the rest and only re-does what's affected.")
            new_files = st.file_uploader("new", accept_multiple_files=True, label_visibility="collapsed",
                                         key=f"late-{S.get('slug')}-{S.get('run_dir')}")
            if st.button("Add & update", type="primary", width="stretch", disabled=not new_files, key="add-new"):
                add_new = ("files", new_files)
            if (workspace.SAMPLES / S.get("slug", "") / "late").exists():
                if st.button("Use this sample's late files", width="stretch", key="add-late"):
                    add_new = ("late", None)
    run_label = "Run again" if d else "Start the close"
    has_bank = bool(close.load_bank(ws))
    start = controls[2].button(run_label, type="primary", width="stretch", disabled=READ_ONLY or not has_bank,
                               key="start", help=None if has_bank else "Add a bank statement in Your month first")
    line_box, feed_box = st.empty(), st.empty()

    def title(text: str, pill: str, ok: bool):
        title_box.html(f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">'
                       f'<span class="title" style="margin:0">{text}</span>'
                       f'<span class="{"pill-ok" if ok else "pill-wait"}">{pill}</span></div>')

    if d:
        f = d["facts"]
        title("September is closed." if f["balanced"] else "Not closed yet.",
              "Books match the bank · ₹0" if f["balanced"] else f"Off by {ui.inr(f['bank_gap'])}", f["balanced"])
    else:
        title(f"{biz['name']}", "Ready when you are", False)
    states = S.get("states") or ({k: "done" for k, *_ in ui.TEAM} if d else {})
    bubbles = S.get("bubbles") or (recorded_bubbles() if d else {})
    owner_says = "Thanks, team! 🙏" if d and d["facts"]["balanced"] else "Close September, please"
    line_box.html(ui.line(states, bubbles, owner_says))

    previous = None
    if add_new and d:
        previous = {"entries": d["entries"], "facts": d["facts"], "actions": d["actions"]}
        if add_new[0] == "late":
            added = workspace.add_late_arrivals(ws, S["slug"])
            S.setdefault("new_files", []).extend(x.split(" →")[0] for x in added)
        else:
            for nf in add_new[1]:
                workspace.add_file(ws, nf.name, nf.getvalue())
                S.setdefault("new_files", []).append(nf.name)
    if (start or add_new or S.pop("autostart", False)) and not READ_ONLY and has_bank and allowed("closes"):
        title("The team is working…", "about a minute", False)
        run_close(line_box, feed_box, previous=previous, owner_says="Close September, please")
        st.rerun()
    if READ_ONLY:
        st.info("Read-only demo: showing the recorded close. Run locally with API keys to watch the team work live.")
    if not d:
        return

    f, a = d["facts"], d["actions"]
    t = f["tax"]
    owed = sum(Decimal(i["open"]) for i in f.get("open_invoices", []))
    r = st.columns(4)
    r[0].html(f'<div class="res"><div class="l">Profit</div><div class="v">{ui.inr(t["profit"])}</div></div>')
    r[1].html(f'<div class="res"><div class="l">Set aside for tax</div><div class="v">{ui.inr(t["set_aside"])}</div></div>')
    r[2].html(f'<div class="res"><div class="l">Clients owe you</div><div class="v">{ui.inr(owed)}</div></div>')
    names = {"duplicate_post": "duplicate bill", "amount_mismatch": "vendor error"}
    fixed = " · ".join(f"{ui.inr(abs(Decimal(h['effect'])))} {names.get(h['kind'], h['kind'])}" for h in f.get("gap_hunt", []))
    r[3].html(f'<div class="res amber"><div class="l">Fixed during the close</div>'
              f'<div style="font-size:14px;margin-top:6px">{fixed or "Nothing needed fixing"}</div></div>')
    with r[1].popover("How is tax worked out?", width="stretch"):
        st.markdown(f"**Estimate from your settings** (not a filing):  \n"
                    f"- GST collected {ui.inr(t['output_tax_collected'])} − claimable {ui.inr(t['input_tax_claimable'])} "
                    f"= **{ui.inr(t['net_indirect_tax'])}**  \n"
                    f"- Income-tax provision {Decimal(t['assumptions']['income_tax_provision_rate']):.0%} of profit "
                    f"= **{ui.inr(t['income_tax_provision'])}**")
    st.html('<div style="height:4px"></div>')
    c = st.columns(2, gap="medium")
    with c[0]:
        approvals(a)
        with st.container(border=True):
            if f.get("changes"):
                st.html('<div class="panel-h" style="color:#F2B84B">What changed</div>')
                for ch in f["changes"]:
                    st.markdown(f"- {ch}")
            else:
                st.html('<div class="panel-h">What changed</div>')
                st.caption("Nothing yet. Use **+ Something new arrived** when a late bill or payment shows up.")
    with c[1]:
        chat_box(d)


def approvals(a: dict) -> None:
    decided, links = S.setdefault("decided", {}), S.setdefault("links", {})
    items = ([("invoice", i, f"🧾 Invoice {i['client'].split()[0]} {ui.inr(i['total'])}") for i in a["invoices"]]
             + [("reminder", r, f"⏰ Remind {r['client'].split()[0]} {ui.inr(r['open'])}") for r in a["reminders"]]
             + [("bill", m, f"📎 Bill from {m['payee'].split('-')[-1].split('*')[-1][:14].title()} {ui.inr(m['amount'])}")
                for m in a["missing_bills"]])
    with st.container(border=True):
        st.html(f'<div class="panel-h">Needs your OK · {sum(1 for k, *_ in items) - sum(1 for v in decided.values() if v)}</div>')
        if not items:
            st.caption("Nothing to approve.")
        for kind, item, label in items:
            key = f"{kind}-{label}"
            cc = st.columns([3, 2])
            cc[0].markdown(f"{'✅ ' if decided.get(key) == 'approved' else ''}{label}")
            if decided.get(key) != "approved":
                if cc[1].button("Approve", key=f"ok-{key}", type="primary", width="stretch", disabled=READ_ONLY):
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
                cc[1].link_button("Pay link", links[key], width="stretch")


def chat_box(d: dict) -> None:
    history = S.setdefault("chat", [])
    with st.container(border=True):
        st.html('<div class="panel-h">Ask Munshi</div>')
        for h in history[-3:]:
            st.chat_message("user").write(h["q"])
            st.chat_message("assistant", avatar="🧾").write(h["a"])
        q = None
        cols = st.columns(2)
        if cols[0].button("Who owes me?", width="stretch", disabled=READ_ONLY, key="q1"):
            q = "Who owes me money?"
        if cols[1].button("Safe to spend?", width="stretch", disabled=READ_ONLY, key="q2"):
            q = "After setting aside tax, how much can I safely spend this month?"
        with st.form("ask-form", border=False, clear_on_submit=True):
            typed = st.text_input("Ask about your books", label_visibility="collapsed",
                                  placeholder="Ask about your books…", disabled=READ_ONLY)
            if st.form_submit_button("Ask", width="stretch", disabled=READ_ONLY) and typed:
                q = typed
        if q and allowed("questions"):
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
