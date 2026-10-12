# neatHack build log: Munshi

## Project
**Munshi**: an AI CA that closes a messy month of books, recovers when they don't balance, and proves every number.
Problem: every business needs its books kept, invoices raised, money chased and tax set aside, and most can't afford a CA
every day. Owners do it at midnight or see their accountant once a month, working from chaos.

## Team
Shivam Kumar (solo) · team name "Superposition"

## Stack
Python 3.12 · beancount (double-entry ledger + validation) · OpenAI-compatible client → neatHack LiteLLM (Nova Lite,
Claude Haiku, Claude Sonnet 4.6) and TokenRouter (development) · **neatlogs** Python SDK (sessions, spans, end-user,
tags) · **Entire** (checkpoints, entire-graph) · **Crustdata** company API · **SEC EDGAR** XBRL API · **Dodo Payments**
(test mode) · Streamlit · pdfplumber · reportlab/Pillow (demo data generation)

## Build log
### 2026-10-11 (day 2)
- Chose the idea after reviewing sponsors; wrote the design pack (`docs/idea/`). An external review narrowed
  scope to one hero loop: close one month, recover when it doesn't balance, prove the result.
- Scaffolded the repo; neatlogs connected (SDK doctor probe passes: trace visible + finalized); Entire enabled + logged in.
- **Data:** searched for public real Indian invoice datasets and found none. Decision: hybrid. Demo business generated
  (labelled), reader benchmarked on **361 real SROIE receipts**. Generated Studio Kaveri Sep-2026 with 12 traps + answer key
  (a test proves the answer key itself balances).
- **Ledger:** beancount writer, deterministic balance check, gap hunt + safe repair (tests).
- **Reader:** cheap-first extraction, arithmetic checks in code, strong re-read; first run caught the planted vendor
  error (₹5,000 + ₹900 ≠ ₹6,100) as a vendor error, not a misread.
- **Integrations:** Dodo test-mode payment links (product + checkout session) ✅; Crustdata identify/enrich (domain lookup
  is precise, name lookup ambiguous, so domain first) ✅; SEC EDGAR peers by industry code ✅ (feed names are garbled →
  names taken from company facts).
- **v2 pipeline:** research → read → match → enter bills → categorise → reconcile → gap hunt → tax → actions → brief →
  commit books. First full run: balanced after gap hunt, 12/12 traps.
- **Evidence runs on neatHack models:** v1 ✗ off by ₹9,050, 2/12 traps, brief states wrong profit (₹98,685 vs true
  ₹58,367) · v2 ✅ ₹0, 12/12 traps, 100% categorisation, tax exact, 9,274 tokens (v1: 13,061).
- Business plan built from measured usage (₹1.39 model cost per demo close at list prices; 92.7% gross margin).

## Demo
`uv run streamlit run app/streamlit_app.py` → "Close the month". Video: (link added at submission)

## Known limitations and next steps
See README "Known limitations". Next: real business data pilot, owner Q&A in the app, Dodo webhooks on a public
endpoint, Entire agent integration so `entire why` explains ledger lines, peer filtering by business description.

## Submission
- [x] Public repo with commits dated during the hackathon
- [x] neatlogs traces (v1/v2 sessions)
- [x] Entire enabled + graph output
- [x] Business plan from measured costs (`evidence/business-plan/`)
- Note: cfo.ai not used (its signup requires a payment card)
- [ ] Demo video ≤ 3 min
- [ ] Building-in-public links
- [ ] Quote post on X (Oct 12, 7:00–11:55 PM IST)
