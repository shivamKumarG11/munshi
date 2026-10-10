# 02: Product (v3)

## Pitch
> **Munshi is an AI CA that closes a messy month of books, recovers when they don't balance, and proves every number.**

## The owner's experience
1. **Add the business.** Name + what it does. **Munshi researches it**: what the company does and its size (Crustdata), plus **real peer companies' filed financials** (SEC EDGAR / Companies House) to learn what "normal" looks like for this kind of business.
2. **Drop in the month.** Bank statement (CSV) + bills, receipts and invoices (PDFs, photos).
3. **Munshi closes the month.** Live progress: reading → categorising → matching → **checking the balance** → (if off) **hunting the gap** → closed.
4. **Munshi asks only what it can't know.** *"₹12,000 to 'R. SHARMA': salary, contractor, or personal?"* One tap, remembered next time.
5. **Approve actions.** Drafts (an invoice for un-billed work with a payment link, a request for a missing bill): nothing goes out without the owner's OK.
6. **Read the brief.**

### The morning brief
> **September is closed ✅**: books balance to the bank (₹0 difference)
> - **Profit:** ₹3.2L (revenue ₹9.8L, expenses ₹6.6L)
> - **Compared with real peers** (filed accounts of similar agencies): software spend 9% of revenue vs peers' 4%
> - **Tax to set aside:** ≈ ₹58k: *estimate from your settings* (tax on sales 18%, claimable tax on purchases, income-tax provision 25% of profit) [see assumptions]
> - **📎 Missing paperwork:** 3 payments (₹71k) without a bill, so not claimable yet; requests drafted
> - **🧾 Never invoiced:** Zenith job from the timesheet: ₹65k invoice drafted with a payment link
> - **💸 Overdue:** Acme ₹1.2L, 38 days, reminder drafted
>
> *Every number links to the ledger line and its source document.*

## Scope tiers
| CORE (the demo depends on it) | SHOULD (cheap, meaningful) | STRETCH (only if core is solid) |
| --- | --- | --- |
| Read bank CSV + documents, with code checks | Crustdata payee lookup for cryptic narrations | Multi-company review mode (portfolio of real public companies) |
| Categorise with evidence + owner questions | Peer benchmarks from EDGAR / Companies House in the brief | Dodo webhook → auto-post payment to ledger |
| Match (duplicates, one-to-many, partials) | Draft invoice + **Dodo payment link** (test mode) | cfo.ai sync via MCP (core uses CSV upload) |
| beancount ledger + balance check + **gap hunt** | Missing-bill + overdue drafts | `entire-agent-munshi` (`entire why` on ledger lines) |
| Tax-to-set-aside estimate (assumptions shown) | | AWS hosting (always-on, webhooks) |
| Morning brief computed from the ledger | | Ask-anything chat |
| neatlogs tracing + v1/v2 evidence | | |
| cfo.ai business plan + actuals CSV into cfo.ai | | |

## Out of scope (stated in the README)
- Tax filing; jurisdiction-specific rules (the estimate uses the owner's configured rates).
- Live bank connections.
- Payroll.
- Claiming the demo is a real business's books: **documents are real (public datasets), the bank statement is generated from them, peer financials are real filings.**

## Screens (Streamlit)
1. **Setup + research:** business profile, the peers Munshi chose, their key ratios.
2. **Close run:** live steps; the balance check (red ✗ → gap hunt → green ✅). **The demo screen.**
3. **Books:** P&L; click any number → ledger lines → document + reasoning.
4. **Actions:** drafts to approve.
5. **Brief.**
