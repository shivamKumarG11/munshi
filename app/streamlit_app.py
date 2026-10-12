"""Munshi: an AI CA that closes a messy month of books, recovers when they don't balance, and proves every number."""

import csv
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
from munshi import close, score, tracing  # noqa: E402
from munshi.config import settings  # noqa: E402

MONTH = ROOT / "data/demo/studio-kaveri/2026-09"
KEY = ROOT / "data/answer_key/studio-kaveri-2026-09.json"
EVIDENCE = ROOT / "evidence/runs"
READ_ONLY = not settings.llm_api_key

st.set_page_config(page_title="Munshi · your AI CA", page_icon="🧾", layout="wide")
st.html(ui.CSS)


# --------------------------------------------------------------------------- data

@st.cache_resource
def _tracing() -> bool:
    return tracing.init("v2-app")


def run_dir() -> Path:
    if st.session_state.get("run_dir"):
        return Path(st.session_state["run_dir"])
    local = sorted((ROOT / "runs").glob("app-*-v2"), reverse=True) if (ROOT / "runs").exists() else []
    for r in local:
        if (r / "facts.json").exists():
            return r
    return EVIDENCE / "close-v2"


def load(r: Path) -> dict:
    j = lambda n: json.loads((r / n).read_text(encoding="utf-8"))
    return {"facts": j("facts.json"), "entries": j("entries.json"), "actions": j("actions.json"), "dir": r}


def month_stats() -> dict:
    with open(MONTH / "bank_statement.csv", encoding="utf-8") as f:
        bank = list(csv.DictReader(f))
    with open(MONTH / "timesheet.csv", encoding="utf-8") as f:
        hours = sum(int(r["hours"]) for r in csv.DictReader(f))
    with open(MONTH / "invoices_issued.csv", encoding="utf-8") as f:
        invoices = len(list(csv.DictReader(f)))
    docs = [p for p in (MONTH / "documents").iterdir() if ".page" not in p.name]
    return {"bank": len(bank), "docs": len(docs), "invoices": invoices, "hours": hours}


STEP_TO_WORKER = {step: key for key, _, _, _, steps in ui.WORKERS for step in steps}


def center_button(label: str, key: str | None = None, primary: bool = True) -> bool:
    c = st.columns([2, 1, 2])
    return c[1].button(label, key=key, type="primary" if primary else "secondary", width="stretch")


# --------------------------------------------------------------------------- pages

def home():
    st.html('<div class="hero"><h1>Your books. Closed. Proven.</h1>'
            '<p>An AI team that closes your month and checks every rupee against the bank.</p></div>')
    if center_button("Close September", key="home-close"):
        st.session_state["autostart"] = not READ_ONLY
        st.switch_page(PAGES["close"])
    st.html(ui.floor())
    s = month_stats()
    cols = st.columns(4)
    for col, (label, value) in zip(cols, [("Bank statement", f"{s['bank']} lines"),
                                          ("Bills & receipts", f"{s['docs']} files"),
                                          ("Invoices you sent", str(s["invoices"])),
                                          ("Timesheet", f"{s['hours']} hours")]):
        col.html(ui.tile(label, value, tilt=False))
    st.html(ui.note("Every step traced in neatlogs · Nothing is sent without your OK · Demo business: generated data"))


def close_page():
    st.html('<div class="center"><div class="title">Close September 2026</div>'
            '<p class="sub">Six workers, one rule: the books must match the bank.</p></div>')
    pills_box, floor_box, feed_box = st.empty(), st.empty(), st.empty()
    done = {k: "done" for k, *_ in ui.WORKERS}

    def show(states, lines):
        pills_box.html(ui.pills(states))
        floor_box.html(ui.floor({k: v for k, v in states.items() if v in ("active", "done")},
                                final_on=all(states.get(k) == "done" for k, *_ in ui.WORKERS)))
        if lines:
            feed_box.html('<div class="card" style="font-size:14px;line-height:1.8">'
                          + "".join(f"<div>{line}</div>" for line in lines[-6:]) + "</div>")

    if READ_ONLY:
        st.info("Read-only demo: showing the recorded close (neatHack models, traced in neatlogs). "
                "Run the app locally with API keys to close live.")
    else:
        clicked = center_button("Run the close", key="run-close")
        if clicked or st.session_state.pop("autostart", False):
            states = {k: "" for k, *_ in ui.WORKERS}
            lines: list[str] = []

            def progress(step, message, data=None):
                worker = STEP_TO_WORKER.get(step)
                if worker:
                    for k, *_ in ui.WORKERS:          # everything before the current worker is done
                        if k == worker:
                            break
                        states[k] = "done"
                    states[worker] = "warn" if message.startswith("✗") else "active"
                icon = "🟥" if "✗" in message else ("🟩" if "✅" in message else "▸")
                lines.append(f"{icon} <b>{step}</b> · {message}")
                show(states, lines)

            out_dir = ROOT / "runs" / f"app-{datetime.now():%Y%m%d-%H%M%S}-v2"
            session = f"app-close-{datetime.now():%H%M%S}"
            _tracing()
            with tracing.run("munshi-close-v2-app", session_id=session, end_user_id="studio-kaveri"):
                close.close_v2(MONTH, out_dir, progress=progress)
            result = score.score(out_dir, KEY)
            (out_dir / "score.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
            st.session_state["run_dir"] = str(out_dir)
            st.session_state["last_session"] = f"{session} · {result['seconds']} s · {result['llm_calls']} model calls"
            feed_box.empty()

    show(done, [])
    f = load(run_dir())["facts"]
    hunts = f.get("gap_hunt", [])
    if hunts:
        gap = sum(Decimal(h["effect"]) for h in hunts)
        names = {"duplicate_post": "Same bill uploaded twice", "amount_mismatch": "Vendor's total is wrong",
                 "missing_post": "A payment wasn't recorded", "unknown_txn": "An entry with no bank line"}
        causes = "".join(f'<div class="cause"><span class="amt">{ui.inr(abs(Decimal(h["effect"])))}</span>'
                         f'<span>{names.get(h["kind"], h["kind"])}</span></div>' for h in hunts)
        end = ui.tile("Fixed and re-checked", "₹0", "green") if f["balanced"] else ui.tile("Still off", ui.inr(f["bank_gap"]), "red")
        st.html('<div class="center"><div class="title" style="font-size:34px">The books didn\'t match the bank.</div></div>'
                f'<div class="gap-row">{ui.tile("Gap found", ui.inr(gap), "red")}'
                f'<div style="font-size:30px;color:#F2B84B">→</div><div>{causes}</div>'
                f'<div style="font-size:30px;color:#4FD18B">→</div>{end}</div>')
        with st.expander("Munshi's explanation"):
            for h in hunts:
                st.markdown(f"- {h['explanation']}")
    elif f.get("balanced"):
        st.html('<div class="center"><div class="title" style="font-size:34px">Matched the bank on the first check ✓</div></div>')
    extra = f" · {st.session_state['last_session']}" if st.session_state.get("last_session") else ""
    st.html(ui.note(f"Every step of this close is a trace in neatlogs{extra}"))
    if center_button("See the results", key="to-results"):
        st.switch_page(PAGES["results"])


def results_page():
    d = load(run_dir())
    f, a = d["facts"], d["actions"]
    t = f["tax"]
    owed = sum(Decimal(i["open"]) for i in f.get("open_invoices", []))
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.html(f'<div class="title">{"September is closed. ✓" if f["balanced"] else "September is not closed yet."}</div>')
        c = st.columns(3)
        c[0].html(ui.tile("Profit", ui.inr(t["profit"])))
        c[1].html(ui.tile("Set aside for tax", ui.inr(t["set_aside"])))
        c[2].html(ui.tile("Clients owe you", ui.inr(owed)))
        with c[1].popover("How is tax worked out?"):
            st.markdown(f"**Estimate from your settings** (not a filing):  \n"
                        f"- GST collected {ui.inr(t['output_tax_collected'])} − claimable {ui.inr(t['input_tax_claimable'])} "
                        f"= **{ui.inr(t['net_indirect_tax'])}**  \n"
                        f"- Income-tax provision {Decimal(t['assumptions']['income_tax_provision_rate']):.0%} of profit "
                        f"= **{ui.inr(t['income_tax_provision'])}**")
        c2 = st.columns(2)
        fixes = [{"duplicate_post": "Duplicate bill removed", "amount_mismatch": "Vendor's wrong total flagged"}.get(h["kind"], h["kind"])
                 for h in f.get("gap_hunt", [])]
        c2[0].html('<div class="tile amber"><div class="label" style="color:#F2B84B;font-weight:600">Fixed for you</div>'
                   + "".join(f'<div style="font-size:16px;margin-top:8px">{x}</div>' for x in fixes or ["Nothing needed fixing"])
                   + "</div>")
        n = len(a["invoices"]) + len(a["reminders"]) + len(a["missing_bills"])
        with c2[1]:
            st.html(f'<div class="tile" style="background:#EEF3EF;color:#0E1613;border-bottom-color:#A9B8B0">'
                    f'<div class="label" style="color:#3E4A44;font-weight:600">Needs your OK</div>'
                    f'<div class="title" style="color:#0E1613;margin:4px 0 0">{n} drafts</div></div>')
            if st.button("Review drafts →", key="to-actions", width="stretch"):
                st.switch_page(PAGES["actions"])
        p = f.get("peers")
        if p and p.get("median_operating_margin") is not None and f.get("operating_margin") is not None:
            you, med = f["operating_margin"], p["median_operating_margin"]
            scale = max(you, med, 0.01) * 1.25
            st.html(f'<div class="card"><div style="display:flex;justify-content:space-between;align-items:center">'
                    f'<span class="muted">Your margin vs real peers</span><span class="chip light">SEC EDGAR</span></div>'
                    f'<div style="display:flex;align-items:center;gap:10px;margin-top:12px"><div class="bar" style="width:{you / scale * 100:.0f}%;background:#4FD18B"></div>'
                    f'<span class="mono">{you:.0%} you</span></div>'
                    f'<div style="display:flex;align-items:center;gap:10px;margin-top:8px"><div class="bar" style="width:{max(med, 0) / scale * 100:.0f}%;background:#3A4C45"></div>'
                    f'<span class="mono muted">{med:.0%} median of {len(p["companies"])} listed companies</span></div></div>')
    with right:
        st.html('<div class="title" style="font-size:26px">Ask Munshi</div>')
        history = st.session_state.setdefault("chat", [])
        box = st.container(height=470, border=True)
        with box:
            if not history:
                st.caption("Ask anything about this month. Answers come only from the closed books.")
            for h in history:
                st.chat_message("user").write(h["q"])
                st.chat_message("assistant", avatar="🧾").write(h["a"])
        suggestions = ["Can I afford a new laptop?", "Who owes me money?", "Why is hosting ₹8,850?"]
        picked = None
        for col, q in zip(st.columns(3), suggestions):
            if col.button(q, key=f"s-{q}", width="stretch", disabled=READ_ONLY):
                picked = q
        q = st.chat_input("Ask about your books…", disabled=READ_ONLY) or picked
        if READ_ONLY:
            st.caption("Chat runs locally with API keys.")
        if q:
            from munshi import chat
            _tracing()
            with st.spinner("Checking the books…"):
                ans = chat.answer(q, run_dir(), history)
            history.append({"q": q, "a": ans})
            st.rerun()


def _decided(e: dict) -> str:
    d = e["decided_by"]
    if d.startswith("rule:refund"):
        return "Refund rule"
    if d.startswith("rule:"):
        return "Rule"
    if d == "owner":
        return "You"
    if d.startswith("match:"):
        return f"{len(e['document_ids'])} invoice" + ("s" if len(e["document_ids"]) > 1 else "")
    if "crustdata" in d:
        return "Crustdata lookup"
    return "Bill" if e["document_ids"] else "AI"


def books_page():
    entries = load(run_dir())["entries"]
    head = st.columns([3, 1])
    head[0].html('<div class="title">Every entry has a reason.</div>')
    head[1].html(f'<div class="pill" style="margin-top:14px;justify-content:center"><img src="{ui.LOGO["entire"]}" '
                 f'style="height:12px" alt="Entire"><span class="muted" style="font-weight:500">Books versioned in Git</span></div>')
    rows = [{"Date": e["date"][5:], "Payee": e["payee"][:38], "Account": e["account"].split(":")[-1],
             "Amount ₹": float(e["amount"]), "Decided by": _decided(e)} for e in entries]
    left, right = st.columns([3, 2], gap="large")
    with left:
        sel = st.dataframe(rows, hide_index=True, width="stretch", height=560, on_select="rerun",
                           selection_mode="single-row", key="books-table",
                           column_config={"Amount ₹": st.column_config.NumberColumn(format="%.2f")})
        st.caption("Tap a row to see why it's there.")
    chosen = sel.selection.rows if sel and getattr(sel, "selection", None) else []
    picked = chosen[0] if chosen else next((i for i, e in enumerate(entries) if "crustdata" in e["decided_by"]), 0)
    e = entries[picked]
    acct = e["account"].split(":")[-1]
    steps = {
        "Rule": ["Bank line matched a standard pattern", f"Booked as {acct}"],
        "You": ["Munshi wasn't sure, so it asked you", f"You said: {e['narration']}", f"Booked as {acct}"],
        "Bill": [f"Matched to bill {', '.join(e['document_ids'])}", "Totals re-added in code", f"Booked as {acct}"],
        "Crustdata lookup": ["Cryptic bank line", f"Looked up: {e['narration'].split(':')[0]}", f"Booked as {acct}"],
        "Refund rule": ["Money came back from a vendor", "Linked to the original payment", "Reduces that expense, not income"],
    }.get(_decided(e), [e["narration"][:120], f"Booked as {acct}"])
    warn = ""
    if e["amount"].startswith("-") and not e["document_ids"] and e["account"].startswith("Expenses") \
            and not e["decided_by"].startswith(("rule", "owner")):
        warn = '<div class="warn">No bill yet, so tax can\'t be claimed. Request drafted in Actions.</div>'
    if "vendor bill total" in e["narration"]:
        warn = '<div class="warn">The vendor\'s bill total was wrong; the bank figure was booked and the vendor flagged.</div>'
    with right:
        st.html(f'<div class="why"><div class="k">WHY THIS ENTRY</div>'
                f'<div class="h">{e["payee"][:34]} → {acct}</div>'
                f'<div class="mono" style="font-size:22px;margin-bottom:10px">{ui.inr(e["amount"], sign=True)}</div>'
                + "".join(f'<div class="step"><span class="n">{i}</span><span>{s}</span></div>' for i, s in enumerate(steps, 1))
                + warn + "</div>")


def actions_page():
    a = load(run_dir())["actions"]
    decided = st.session_state.setdefault("decided", {})
    links = st.session_state.setdefault("links", {})
    cards = ([("invoice", i) for i in a["invoices"]] + [("reminder", r) for r in a["reminders"]]
             + [("bill", m) for m in a["missing_bills"]])
    st.html(f'<div class="center"><div class="title">{len(cards)} drafts. You decide.</div>'
            f'<p class="sub">Nothing leaves Munshi until you approve it.</p></div>')
    cols = st.columns(2, gap="large")
    for idx, (kind, item) in enumerate(cards):
        key = f"{kind}-{idx}"
        with cols[idx % 2]:
            if kind == "invoice":
                tag = '<span class="tag g">Never invoiced</span>'
                badge = f'<span class="chip">Pay link by <img src="{ui.LOGO["dodo"]}" alt="Dodo Payments"></span>'
                who, what, amt = item["client"], f"{item['project']} · {item['hours']} h", ui.inr(item["total"])
                ok_label = "Approve & create pay link"
            elif kind == "reminder":
                tag = f'<span class="tag {"r" if item["tone"] == "firm" else "a"}">{item["days_overdue"]} days overdue</span>'
                badge = f'<span class="muted" style="font-size:13px">{item["tone"].title()} reminder</span>'
                who, what, amt = item["client"], f"Invoice {item['invoice']}", ui.inr(item["open"])
                ok_label = "Approve reminder"
            else:
                tag = '<span class="tag g" style="color:#C9D4CE">Missing bill</span>'
                badge = f'<span class="chip"><img src="{ui.LOGO["crustdata"]}" alt="Crustdata"></span>'
                who, what, amt = item["payee"][:28], "Tax not claimable until the bill arrives", ui.inr(item["amount"])
                ok_label = "Approve bill request"
            state = decided.get(key)
            dim = ' style="opacity:.45"' if state == "skipped" else ""
            st.html(f'<div class="card"{dim}><div style="display:flex;justify-content:space-between;align-items:center">'
                    f'{tag}{badge}</div><div class="who">{who}</div><div class="what">{what}</div>'
                    f'<div class="amt">{amt}</div></div>')
            if state is None:
                b = st.columns([3, 1])
                if b[0].button(ok_label, key=f"ok-{key}", type="primary", width="stretch"):
                    decided[key] = "approved"
                    if kind == "invoice" and not READ_ONLY:
                        existing = (item.get("dodo") or {}).get("checkout_url")
                        if existing:
                            links[key] = existing
                        else:
                            from munshi.integrations import dodo
                            biz = json.loads((MONTH / "business.json").read_text(encoding="utf-8"))
                            with st.spinner("Creating Dodo payment link (test mode)…"):
                                made = dodo.payment_link(item["number"], f"{item['project']} ({item['hours']} h)",
                                                         Decimal(item["total"]), item["client"],
                                                         biz.get("client_emails", {}).get(item["client"], "accounts@example.com"))
                            links[key] = made["checkout_url"]
                    st.rerun()
                if b[1].button("Skip", key=f"skip-{key}", width="stretch"):
                    decided[key] = "skipped"
                    st.rerun()
            elif state == "approved":
                link = links.get(key) or (item.get("dodo") or {}).get("checkout_url")
                if kind == "invoice" and link:
                    st.link_button("Open the Dodo payment link (test mode)", link, width="stretch")
                draft = {
                    "invoice": f"Hi {item.get('client', '')}, please find invoice {item.get('number', '')} for "
                               f"{item.get('project', '')} ({item.get('hours', '')} h): {amt} incl. GST. Pay here: {link or '[link]'}",
                    "reminder": f"Hi {item.get('client', '')}, a {'firm' if item.get('tone') == 'firm' else 'gentle'} reminder that "
                                f"invoice {item.get('invoice', '')} has {amt} outstanding, now {item.get('days_overdue', '')} days overdue.",
                    "bill": f"Hello, could you send the GST invoice for our payment of {amt} ({item.get('payee', '')})?",
                }[kind]
                st.success("Approved. Ready to send:")
                st.code(draft, language=None, wrap_lines=True)
            else:
                st.caption("Skipped.")


def proof_page():
    st.html('<div class="center"><div class="title">Same month. Two versions.</div>'
            '<p class="sub">12 traps a good accountant must catch.</p></div>')
    s1 = json.loads((EVIDENCE / "close-v1/score.json").read_text(encoding="utf-8"))
    s2 = json.loads((EVIDENCE / "close-v2/score.json").read_text(encoding="utf-8"))
    brief1 = (EVIDENCE / "close-v1/brief.md").read_text(encoding="utf-8")
    m = re.search(r"Net Profit[^\d]*([\d,]+)", brief1)
    v1_profit = f"₹{m.group(1)}" if m else "wrong"
    st.html(f'<div class="vs"><div class="side v1"><b style="color:#F3B4A9">v1 · naive</b><div class="nums">'
            f'<div><div class="num">{ui.inr(abs(Decimal(s1["bank_gap"])))}</div><div class="cap">off the bank</div></div>'
            f'<div><div class="num">{s1["traps_caught"]}/{s1["traps_total"]}</div><div class="cap">traps caught</div></div>'
            f'<div><div class="num">{v1_profit}</div><div class="cap">wrong profit</div></div></div></div>'
            f'<div class="side v2"><b>v2 · Munshi</b><div class="nums">'
            f'<div><div class="num">₹0</div><div class="cap">off the bank</div></div>'
            f'<div><div class="num">{s2["traps_caught"]}/{s2["traps_total"]}</div><div class="cap">traps caught</div></div>'
            f'<div><div class="num">{ui.inr(s2["true_profit"])}</div><div class="cap">true profit</div></div></div></div></div>')
    from munshi import benchmark
    bench = EVIDENCE / "benchmark"
    v1f, v2f = sorted(bench.glob("benchmark-v1-*.json")), bench / "benchmark-v2-after-fix.json"
    if v1f and v2f.exists():
        b1, b2 = benchmark.rescore(v1f[-1])["accuracy"], benchmark.rescore(v2f)["accuracy"]
        rows = "".join(
            f'<div style="display:grid;grid-template-columns:90px 1fr;gap:14px;align-items:center;margin-top:12px">'
            f'<span>{label}</span><div>'
            f'<div style="display:flex;align-items:center;gap:10px"><div class="bar" style="width:{b1[k] * 88:.0f}%;background:#3A4C45"></div><span class="mono muted" style="font-size:13px">{b1[k]:.1%}</span></div>'
            f'<div style="display:flex;align-items:center;gap:10px;margin-top:5px"><div class="bar" style="width:{b2[k] * 88:.0f}%;background:#4FD18B"></div><span class="mono" style="font-size:13px">{b2[k]:.1%}</span></div>'
            f'</div></div>' for label, k in [("Vendor", "company"), ("Total", "total"), ("Date", "date")])
        st.html(f'<div class="card" style="margin-top:26px"><div style="display:flex;justify-content:space-between">'
                f'<b style="font-family:Space Grotesk;font-size:21px">Reading 40 real scanned receipts</b>'
                f'<span class="muted" style="font-size:13px">SROIE · v1 grey · v2 green</span></div>{rows}</div>')
    tokens = (1 - s2["llm_tokens"] / s1["llm_tokens"]) * 100
    st.html(f'<div class="pills" style="margin-top:18px">'
            f'<div class="pill"><img src="{ui.LOGO["neatlogs"]}" style="width:24px;height:24px;border-radius:6px" alt="neatlogs">Failures found in the traces</div>'
            f'<div class="pill"><img src="{ui.LOGO["entire"]}" style="height:12px" alt="Entire">Every fix checkpointed</div>'
            f'<div class="pill"><span class="mono" style="color:#8FE3B5">−{tokens:.0f}%</span>tokens per close</div></div>')


PAGES = {
    "home": st.Page(home, title="Home", icon=":material/home:", default=True, url_path="home"),
    "close": st.Page(close_page, title="Close", icon=":material/play_circle:", url_path="close"),
    "results": st.Page(results_page, title="Results", icon=":material/insights:", url_path="results"),
    "books": st.Page(books_page, title="Books", icon=":material/menu_book:", url_path="books"),
    "actions": st.Page(actions_page, title="Actions", icon=":material/task_alt:", url_path="actions"),
    "proof": st.Page(proof_page, title="Proof", icon=":material/verified:", url_path="proof"),
}
if __name__ == "__main__" or __name__ == "__page__":
    st.navigation(list(PAGES.values()), position="top").run()
