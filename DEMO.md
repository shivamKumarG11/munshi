# Recording the demo (≤ 3:00)

**Before recording:** `uv run streamlit run app/streamlit_app.py` (keep the neatlogs dashboard and entire.io open in
other tabs). Turn on "Create real Dodo payment links" in the sidebar. Use 1080p, captions on.

| Time | Screen | Say |
| --- | --- | --- |
| 0:00–0:12 | `data/demo/.../documents` folder: bills, a blurry receipt, a bank CSV | "Every business has a CA it can't afford to call every day. This is month-end. Meet Munshi." |
| 0:12–0:25 | README architecture block | "A coordinator agent researches the business, reads every document, matches, categorises, then reconciles against the bank, and doesn't stop until the books balance. Every step is traced in neatlogs." |
| 0:25–1:15 | App → **Close the month** (live log) | Point at: SEC peers found · vendor error on PrintWorks · duplicate CloudNest upload · Notion resolved via Crustdata · **✗ off by ₹9,050** → gap hunt explains both → **✅ ₹0** |
| 1:15–1:40 | neatlogs → session `close-studio-kaveri-2026-09-v2-023726` (or the app's new session) | "Here's that close in neatlogs: the cheap read, the failed check, the Sonnet re-read, the Crustdata lookup, the reconciliation failing then passing." |
| 1:40–2:00 | App → **Evidence** tab | "Version one, same month: off by ₹9,050, caught 2 of 12 traps, and told the owner profit was ₹98,685. It's ₹58,367. v2: balanced, 12 of 12, 30% fewer tokens. On 40 real receipts the reader went from 52% to 70% on vendor names; the benchmark even caught a regression we then fixed." |
| 2:00–2:20 | entire.io checkpoint / `evidence/entire/` graph search + ledger repo `git log` | "Entire keeps the why behind the code; and the books themselves are code: a ledger committed to Git every close." |
| 2:20–2:42 | `evidence/cfo-ai/business_plan.md` (+ cfo.ai if access arrives) | "We priced Munshi on costs neatlogs measured: ₹1.39 of model cost per close, 93% gross margin, break-even in month 13 in the base case." |
| 2:42–3:00 | App → **Brief** + **Actions** (Dodo link) | "Books closed, gaps explained, tax to set aside estimated from your settings, an un-billed job invoiced with a Dodo link. Munshi: every number, proven." |

Say once, plainly: *"The receipts benchmark is real data; the demo business is generated, labelled as such."*
