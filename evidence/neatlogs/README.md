# neatlogs evidence

Every Munshi close is **one neatlogs session**; the business is the **end user** (so cost per customer is
measurable), and runs are tagged `agent_version=v1|v2` and `llm=<provider>`.

## The two evidence runs (same month, same answer key, neatHack LiteLLM models)
| Run | neatlogs session id | Result |
| --- | --- | --- |
| v1 (naive) | `close-studio-kaveri-2026-09-v1-023643` | ✗ books off by ₹9,050 · 2/12 traps · brief states wrong profit |
| v2 (Munshi) | `close-studio-kaveri-2026-09-v2-023726` | ✅ balanced ₹0 · 12/12 traps · brief states true profit |

Search these session ids in the neatlogs **traces** view (workflow `munshi-close`).

## What a v2 trace shows
- Root `munshi-close-v2` → `munshi_close_v2` workflow
- `parse_bank_statement` (TOOL): statement parsed and running balance verified in code
- `research_peers` (AGENT) → `edgar_companies_by_industry`, `edgar_company_ratios` (TOOL)
- `read_document` (AGENT) per bill/receipt, with the LLM call inside; the PrintWorks bill shows the cheap read,
  a failed arithmetic check, and the **strong-model re-read** (recovery) that confirms a vendor error
- `match_bills`, `match_invoice_payments` (TOOL)
- `categorise` (AGENT) per bank line; `crustdata_resolve_company` (TOOL) on `RZP*NOTION LABS`
- the reconciliation: the ledger check fails (gap ₹-9,050), then gap hunt and repair, then re-check passes
- `dodo_payment_link` (TOOL): invoice payment link for un-invoiced work

## How v1's failures were found and fixed (the before → after)
| v1 failure (seen in v1 traces/outputs) | Root cause | v2 fix |
| --- | --- | --- |
| Hosting booked twice (₹17,700) → books off | bills entered as read; no reconciliation | bank reconciliation + gap hunt + duplicate detection by file hash |
| PrintWorks booked at ₹6,100 (vendor's wrong total) | no arithmetic check on documents | code check → strong re-read → vendor error flagged, bank figure booked |
| Refund booked to Contractors | refund categorised without context | refund rule links to the original payment's account |
| Netflix booked as Software | personal spend not questioned | low confidence → owner question; owner answer remembered |
| Brief says profit ₹98,685 (true ₹58,367) | LLM wrote the brief from raw entries | brief computed from the reconciled ledger only |
| Strong model on every call | no routing | cheap first (Haiku/Nova), Sonnet only on failed checks: 13,061 → 9,274 tokens |

## Screenshots to add (from the neatlogs dashboard)
- [ ] `traces-v2-session.png`: the v2 session tree
- [ ] `trace-gap-hunt.png`: the reconciliation failing then passing
- [ ] `trace-vendor-error-reread.png`: cheap read → check fail → Sonnet re-read
- [ ] `analytics-cost.png`: cost per session (v1 vs v2)

## Suggested detections (configure in the dashboard)
- "Books did not balance after gap hunt": fires on facts.balanced = false
- "Strong-model re-read rate > 30%": early warning that documents got harder or the cheap model regressed
- "Owner questions > 5 per close": the categoriser is unsure too often
