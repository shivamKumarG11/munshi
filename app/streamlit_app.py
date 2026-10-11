"""Munshi demo app: close the month live, see the books, the brief, the actions and the evidence."""

import json
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from munshi import close, score, tracing  # noqa: E402
from munshi.config import settings  # noqa: E402

MONTH = ROOT / "data/demo/studio-kaveri/2026-09"
KEY = ROOT / "data/answer_key/studio-kaveri-2026-09.json"
EVIDENCE = ROOT / "runs/evidence"

st.set_page_config(page_title="Munshi: your AI CA", page_icon="🧾", layout="wide")


@st.cache_resource
def _tracing() -> bool:
    return tracing.init("v2-app")


def _latest_run() -> Path | None:
    runs = sorted((ROOT / "runs").glob("app-*-v2"), reverse=True)
    if (EVIDENCE / "close-v2" / "facts.json").exists():
        runs.append(EVIDENCE / "close-v2")
    return next((r for r in runs if (r / "facts.json").exists()), None)


def _load(run: Path) -> dict:
    j = lambda n: json.loads((run / n).read_text(encoding="utf-8"))
    return {"facts": j("facts.json"), "entries": j("entries.json"), "actions": j("actions.json"),
            "brief": (run / "brief.md").read_text(encoding="utf-8"),
            "ledger": (run / "ledger.beancount").read_text(encoding="utf-8"),
            "score": j("score.json") if (run / "score.json").exists() else None, "dir": run}


biz = json.loads((MONTH / "business.json").read_text(encoding="utf-8"))
with st.sidebar:
    st.title("🧾 Munshi")
    st.caption("An AI CA that closes a messy month of books, recovers when they don't balance, and proves every number.")
    st.divider()
    st.markdown(f"**{biz['name']}**  \n{biz['industry']}  \n{biz['address']}")
    st.markdown("**Month:** September 2026")
    st.caption("Demo business, vendors and clients are fictional (generated data). "
               "The reader is benchmarked on 361 real receipts (SROIE).")
    st.divider()
    st.markdown(f"LLM: `{settings.llm_provider}`  \n"
                f"Tracing: {'✅ neatlogs' if _tracing() else '⚠ off (no key)'}")
    live = st.toggle("Create real Dodo payment links (test mode)", value=False)

tab_close, tab_books, tab_brief, tab_actions, tab_research, tab_evidence = st.tabs(
    ["▶ Close the month", "📒 Books", "📰 Brief", "✅ Actions", "🔎 Research", "📊 Evidence"])

with tab_close:
    st.subheader("Close September 2026")
    inputs = sorted(p.name for p in (MONTH / "documents").iterdir() if ".page" not in p.name)
    c1, c2 = st.columns([1, 2])
    c1.markdown("**Inputs**\n\n- `bank_statement.csv`\n- `invoices_issued.csv`\n- `timesheet.csv`\n"
                + "\n".join(f"- `{n}`" for n in inputs))
    with c2:
        if st.button("Close the month", type="primary", use_container_width=True):
            log = st.container(border=True)
            icons = {"plan": "🗂", "research": "🔎", "read": "📄", "match": "🔗", "post": "✏️", "verify": "⚖️",
                     "gap_hunt": "🕵️", "actions": "✅", "brief": "📰"}

            def progress(step, message, data=None):
                style = "error" if message.startswith("✗") else ("success" if message.startswith("✅") else None)
                text = f"{icons.get(step, '•')} **{step}**: {message}"
                (log.error if style == "error" else log.success if style == "success" else log.markdown)(text)

            out_dir = ROOT / "runs" / f"app-{datetime.now():%Y%m%d-%H%M%S}-v2"
            session = f"app-close-{datetime.now():%H%M%S}"
            with st.spinner("Munshi is closing the month…"):
                with tracing.run("munshi-close-v2-app", session_id=session, end_user_id="studio-kaveri"):
                    close.close_v2(MONTH, out_dir, progress=progress, live_actions=live)
                result = score.score(out_dir, KEY)
                (out_dir / "score.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
            st.success(f"Done in {result['seconds']} s · {result['llm_calls']} model calls · "
                       f"traps caught {result['traps_caught']}/{result['traps_total']} · neatlogs session `{session}`")
            st.rerun()

run = _latest_run()
data = _load(run) if run else None

with tab_books:
    if not data:
        st.info("Close the month first.")
    else:
        f = data["facts"]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Balanced to bank", "✅ ₹0" if f["balanced"] else f"✗ {f['bank_gap']}")
        m2.metric("Profit (ex-tax)", f"₹{float(f['tax']['profit']):,.0f}")
        m3.metric("Tax to set aside (estimate)", f"₹{float(f['tax']['set_aside']):,.0f}")
        m4.metric("Evidence coverage", f"{f.get('evidence_coverage', 0):.0%}")
        if f.get("gap_hunt"):
            st.warning("**Found and fixed during the close:**\n\n" + "\n".join(f"- {h['explanation']}" for h in f["gap_hunt"]))
        rows = [{"bank line": e["bank_txn_id"], "date": e["date"], "payee": e["payee"][:42], "account": e["account"],
                 "amount ₹": float(e["amount"]), "tax ₹": float(e["tax"]), "evidence": ", ".join(e["document_ids"]) or "—",
                 "decided by": e["decided_by"], "why": e["narration"][:90]} for e in data["entries"]]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        with st.expander("The ledger (books as code: beancount, committed to Git every close)"):
            st.code(data["ledger"], language="text")

with tab_brief:
    st.markdown(data["brief"] if data else "Close the month first.")
    if data:
        with st.expander("Tax assumptions used for the estimate"):
            st.json(data["facts"]["tax"])

with tab_actions:
    if data:
        a = data["actions"]
        st.markdown("Nothing is sent without your approval.")
        for inv in a["invoices"]:
            with st.container(border=True):
                st.markdown(f"🧾 **Invoice draft {inv['number']}** to {inv['client']}: {inv['project']}, "
                            f"{inv['hours']} h → **₹{float(inv['total']):,.2f}** (incl. GST)")
                if inv.get("dodo", {}).get("checkout_url"):
                    st.link_button("Open Dodo payment link (test mode)", inv["dodo"]["checkout_url"])
        for r in a["reminders"]:
            with st.container(border=True):
                st.markdown(f"⏰ **{r['tone'].title()} reminder**: {r['invoice']} {r['client']}: "
                            f"₹{float(r['open']):,.2f} open, {r['days_overdue']} days overdue")
        for mb in a["missing_bills"]:
            with st.container(border=True):
                st.markdown(f"📎 **Missing bill**: {mb['payee']} ₹{float(mb['amount']):,.2f}. Not claimable until it arrives.")

with tab_research:
    if data and data["facts"].get("peers"):
        p = data["facts"]["peers"]
        st.markdown(f"Real peers Munshi found in SEC EDGAR filings (industries {', '.join(biz['peer_sics'])}). "
                    f"Median operating margin **{p['median_operating_margin']:.1%}**, median effective tax rate "
                    f"**{(p['median_effective_tax_rate'] or 0):.1%}**.")
        st.dataframe([{"company": c["name"], "CIK": c["cik"], "revenue (USD)": f"{float(c['revenue_usd']):,.0f}",
                       "operating margin": f"{c['operating_margin']:.1%}",
                       "effective tax rate": f"{c['effective_tax_rate']:.1%}" if c.get("effective_tax_rate") is not None else "—"}
                      for c in p["companies"]], use_container_width=True, hide_index=True)
        st.caption(p["source"])
    else:
        st.info("Close the month first.")

with tab_evidence:
    st.subheader("Before / after (same month, same answer key, neatHack models)")
    s1, s2 = EVIDENCE / "close-v1" / "score.json", EVIDENCE / "close-v2" / "score.json"
    if s1.exists() and s2.exists():
        v1, v2 = json.loads(s1.read_text()), json.loads(s2.read_text())
        metrics = ["balanced", "bank_gap", "categorisation_accuracy", "exact_entries", "duplicate_posts", "traps_caught",
                   "net_indirect_tax_correct", "llm_calls", "llm_tokens", "seconds"]
        st.dataframe([{"metric": k, "v1 (naive)": str(v1.get(k)), "v2 (Munshi)": str(v2.get(k))} for k in metrics],
                     use_container_width=True, hide_index=True)
        st.dataframe([{"trap": t, "v1": "✅" if v1["traps"][t] else "✗", "v2": "✅" if v2["traps"][t] else "✗"}
                      for t in v2["traps"]], use_container_width=True, hide_index=True)
    else:
        st.info("Evidence runs not found yet (runs/evidence).")
    for f in sorted((ROOT / "runs").glob("benchmark-*.json"))[-2:]:
        b = json.loads(f.read_text(encoding="utf-8"))
        st.markdown(f"**Reader benchmark {b['version']}** on {b['n']} real receipts: {b['accuracy']}")
