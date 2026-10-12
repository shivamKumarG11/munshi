# Munshi 🧾: your business's personal CA

**An AI CA that closes a messy month of books, recovers when they don't balance, and proves every number.**

Built solo for [neatHack](https://neatlogs.com/hackathon) (Oct 10–12, 2026) · track: *Build an agent that works (literally)*

**▶️ [Demo video (2:47)](https://x.com/ShivamKuma31380/status/2109680665235185785)** · **[Live app](https://munshi-bh9x34cncubzjqvgxtzzuy.streamlit.app)**

> Every business has a CA it can't afford to call every day. Munshi is the one you can.

---

## Try it in 3 steps (the app)
`uv run streamlit run app/streamlit_app.py`

1. **Your month:** pick one of three sample businesses (design studio, café, solo consultant) or upload your own
   files. Everything you gave is shown by category (bank lines, bills, receipt photos, invoices sent, timesheet).
2. **The office:** the owner (Kavya) hands the month to six AI workers: Riya (Researcher), Arjun (Reader),
   Meena (Bookkeeper), Dev (Auditor), Sana (Collector), Kabir (Briefer). Watch them work live, approve their drafts,
   ask questions. **Drop a new file at any time** (e.g. a bill that arrived late): Munshi remembers everything
   it already did, processes only what's new, and tells you exactly what changed.
3. **Books & proof:** every entry with the reason behind it, plus the before/after evidence.

## Sample businesses (`samples/`)
| Scenario | Business | What's tricky | Late arrivals (`late/`) |
| --- | --- | --- | --- |
| `01-studio-kaveri` | Design studio, Bengaluru | 12 planted traps (the evidence month) | R. Sharma's invoice; Orbit pays the overdue invoice |
| `02-filter-kaapi-house` | Café, Chennai | Card settlements at 5% GST, no input credit, WhatsApp duplicate, vendor error, school fees from the business account | Fridge-repair bill; a late card settlement |
| `03-arjun-mehta-consulting` | Solo consultant, Pune | One payment for two invoices, partial payment, duplicate hotel invoice, CA fee error, personal purchase | Client pays the balance |

Each has a bank statement, bills (PDF), receipt photos, invoice/timesheet sheets, owner answers, an answer key and a
README. All generated and fictional (`scripts/generate_samples.py`). Results on all three: books balance to ₹0, GST
exact; categorisation 100% / 89% / 100%. Adding the late files costs 0 to 2 model calls.

## What it does
You drop in a month: a bank statement, a pile of bills and receipt photos, the invoices you sent, a timesheet. Munshi closes the month like a careful accountant:

1. **Researches the business**: finds **real peer companies** in SEC EDGAR filings and their margins and tax rates, so it knows what "normal" looks like.
2. **Reads every document**: cheap model first, **arithmetic checked in code**, strong model only when the numbers don't add up. If both models read the same wrong numbers, the **vendor's bill is wrong** and gets flagged, not "fixed".
3. **Matches**: duplicate uploads, one payment covering three invoices, partial payments.
4. **Categorises with evidence**: rules → owner's answers → document → unknown payee looked up in **Crustdata** → asks the owner when unsure. Never guesses silently.
5. **Reconciles against the bank, and doesn't stop until it balances.** Bills are entered as they arrive, then checked against the bank. When the books are off, Munshi **hunts the gap**, explains it, repairs it and re-checks. The balance check is deterministic (beancount), never an LLM opinion.
6. **Acts**: drafts the invoice for work never billed (with a **Dodo Payments** link), reminders for overdue invoices, requests for missing bills. Nothing is sent without approval.
7. **Briefs the owner**: profit, **tax to set aside (an estimate from configured assumptions, shown)**, comparison with real peers, every open item. Every number in the brief comes from the ledger.
8. **Books as code**: each closed month is a plain-text double-entry ledger committed to Git, every line carrying its source document, the decision and who made it.

## Results: v1 → v2 (same month, same answer key, neatHack's Nova/Claude models)
| Metric | v1 (naive) | v2 (Munshi) |
| --- | --- | --- |
| Books balance to the bank | ✗ off by ₹9,050 | ✅ ₹0 after gap hunt |
| Traps caught (of 12) | 2 | **12** |
| Categorisation accuracy | 90.5% | **100%** |
| Brief states the true profit | ✗ said ₹98,685 (true ₹58,367) | ✅ |
| Net GST correct | ✗ | ✅ |
| Tokens per close | 13,061 | **9,274** |
| Reader on 40 **real** receipts (company / date / total) | 52.5% / 100% / 87.5% | **70% / 95% / 90%** |

Full results and the recovery log: [`evidence/results.md`](evidence/results.md).

The demo month contains 12 planted traps a good accountant must catch (see `data/answer_key/`). Reader accuracy is measured separately on **real scanned receipts** (SROIE).

## How each sponsor is used
| Sponsor | Role in Munshi | Evidence |
| --- | --- | --- |
| **neatlogs** | Every close is one traced session (business = end user): every model call, tool call (bank parser, Crustdata, EDGAR, Dodo, ledger check), gap hunt and recovery. v1's failures were found in the traces and fixed in v2 | [`evidence/neatlogs/`](evidence/neatlogs/) |
| **Entire** | Checkpoints on every commit since setup (Claude Code sessions behind each change); the books themselves are versioned in Git, the same "why is this line here?" idea applied to accounting | [`evidence/entire/`](evidence/entire/) |
| **Business plan** | Munshi's own pricing, cost per close (from measured model usage), revenue and runway, 18-month scenarios; each closed month's actuals export as CSV | [`evidence/business-plan/`](evidence/business-plan/) |
| **Dodo Payments** | Payment links on invoices Munshi drafts (test mode); our own usage billing in the plan | `runs/evidence/close-v2/actions.json` |
| **Crustdata** | Resolves cryptic bank narrations (`RZP*NOTION LABS`) to real companies before categorising | traces (`crustdata_resolve_company`) |
| **SEC EDGAR** | Real peer companies and their filed ratios, every figure cited to its filing | Research tab, `facts.json` |

## Data: honest labelling
- **Real:** 361 scanned receipts with expert labels (SROIE, ICDAR 2019, CC BY 4.0) for the reader benchmark; peer financials from SEC EDGAR; company data from Crustdata; Dodo test-mode payments.
- **Generated:** the demo business *Studio Kaveri Design LLP* (fictional), its vendors, clients, bank statement and documents (`scripts/generate_month.py`), because no public dataset of real Indian business documents exists. The answer key is generated alongside, so accuracy is measurable.

## Run it
```bash
uv sync
cp .env.example .env            # add your keys
uv run python scripts/extract_sroie.py      # real receipt benchmark (needs the SROIE parquet)
uv run python scripts/generate_month.py     # demo month + answer key
uv run munshi close --version v2 --live-actions
uv run munshi close --version v1            # the naive baseline
uv run munshi benchmark --n 40 --version v2
uv run streamlit run app/streamlit_app.py   # the demo app
uv run pytest -q
```

## Architecture
```
            ┌────────────────────── close_v2 (coordinator, one neatlogs session) ──────────────────────┐
 research ─▶ read (cheap → checks → strong) ─▶ match ─▶ enter bills ─▶ categorise bank lines ─▶ VERIFY
 (EDGAR)      (vendor-error detection)        (dupes,   (as arrived)   (rules/owner/Crustdata/LLM)    │
                                               1→many,                                     ✗ gap? ─▶ GAP HUNT ─▶ repair ─┐
                                               partial)                                        ▲                       │
                                                                                               └───────────────────────┘
                                                                                     ✅ ─▶ tax ─▶ actions (Dodo) ─▶ brief ─▶ git commit books
```
Code: `src/munshi/`: `close.py` (coordinator), `reader.py`, `matcher.py`, `categoriser.py`, `ledger.py` (beancount + gap hunt), `peers.py` (EDGAR), `integrations/` (Crustdata, Dodo), `score.py`, `benchmark.py`. Design docs: [`docs/idea/`](docs/idea/00-README.md).

## Known limitations
- The demo month is generated (see above); reconciliation has not been tested on a real business's bank data.
- Tax is an **estimate** from configured rates (GST-style collected − claimable, plus an income-tax provision); no filing and no jurisdiction-specific rules.
- Peer selection uses SEC industry codes; some peers (e.g. Groupon under advertising) are loose comparisons.
- Owner answers are pre-filled for the CLI demo (the app is where the owner answers live).
- Dodo payments are polled, not pushed by webhook (no public endpoint during the hackathon).

---
*All code written during neatHack (Oct 10–12, 2026). Build log: [`hackathon.md`](hackathon.md).*
