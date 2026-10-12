# Demo video script (≤ 3:00)

**Setup before recording**
- `uv run streamlit run app/streamlit_app.py` → open http://localhost:8501, browser at 100% zoom, 1440 px wide.
- Pick **Studio Kaveri** (fresh start). Keep these tabs ready: the neatlogs dashboard (Traces), entire.io (or a
  terminal in the repo), and the GitHub repo.
- Record at 1080p, captions on. Say once, plainly: *"The demo business is generated; the reader is benchmarked on
  real receipts."*

| Time | Screen | What to say |
| --- | --- | --- |
| **0:00–0:15** | **1 · Your month**: the category tiles; click **View large** on `printworks-studio-0917.pdf` | "Every business has a CA it can't afford to call every day. This is month-end for a small design studio: 21 bank lines, 9 bills and receipt photos, invoices, a timesheet. Meet Munshi." |
| **0:15–0:25** | Open the **🏢 business picker** briefly (3 samples + New business), close it, click **Hand it to the team →** | "You pick a business, or start your own, and hand the month to the team." |
| **0:25–1:20** | **2 · The office**: the line of workers lights up left to right | "Riya finds real peer companies in SEC filings. Arjun reads every bill. The totals are re-added in code, and he catches a vendor whose bill doesn't add up. Meena categorises every bank line; a cryptic `RZP*NOTION` gets looked up in Crustdata. Then Dev checks the books against the bank: **off by ₹9,050**. He doesn't fudge it. He finds a bill uploaded twice and the vendor's wrong total, fixes both, re-checks: **₹0**." |
| **1:20–1:40** | Results row → **Approve** the Zenith invoice → **Pay link** (Dodo) | "Profit, tax to set aside from your settings, what clients owe. Sana drafted an invoice for work nobody billed. One click, and there's a Dodo payment link. Nothing goes out without the owner's OK." |
| **1:40–2:00** | **+ Something new arrived** → **Use this sample's late files** → the **What changed** panel | "Then real life: a late bill and a client payment arrive. Munshi remembers everything it did; only the affected workers react. Here's exactly what changed: Orbit paid, the reminder is gone, profit updated." |
| **2:00–2:15** | **Ask Munshi** → "Who owes me?" | "And the owner can just ask. Answers come only from the closed books." |
| **2:15–2:35** | **neatlogs** dashboard: the close session (gap hunt + Sonnet re-read) | "Every step is a trace in neatlogs. Our first version was off by ₹9,050, caught 2 of 12 traps and told the owner the wrong profit. We found why in these traces and fixed it." |
| **2:35–2:50** | **3 · Books & proof**: tap the Notion row (Why this entry) + proof tiles; flash `entire why`/checkpoint or the graph output | "Every entry has a reason and the worker who decided it. Now: 12 of 12 traps, ₹0 off the bank, 29% fewer tokens, better on 40 real scanned receipts. The code's history lives in Entire; the books themselves are versioned in Git." |
| **2:50–3:00** | Back to the office line, all ✓ | "Munshi: your books. Closed. Proven." |

**Backup:** if a live run is slow, record the close once and cut the waiting.

**Numbers to quote (all from real runs):** v1 vs v2: ₹9,050 off → ₹0 · traps 2/12 → 12/12 · wrong profit ₹98,685 → true
₹58,367 · tokens 13,061 → 9,274 · real receipts (vendor / total): 52.5% / 87.5% → 70% / 90%.
