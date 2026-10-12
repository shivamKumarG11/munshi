# neatHack submission kit

**Window:** Mon Oct 12, 2026 · 7:00 PM → 11:55 PM IST (Discord has the final say).
**Page:** https://neatlogs.com/submission. Step 1: quote-tweet the official launch post with the demo video attached
and all three required tags (@neatlogs @EntireHQ @arithecfo). Steps 2–3: the form. **Both are required.**

## Step 1: the quote post (275 / 280 characters; attach the video)
```
Our #neatHack submission

Munshi: an AI CA. Six AI workers close a business's month and won't stop until the books match the bank to ₹0.

v1→v2: ₹9,050 off→₹0, traps 2/12→12/12

github.com/shivamKumarG11/munshi

Built with @neatlogs @EntireHQ @dodopayments @crustdata @arithecfo
```
Reply to your own post right after:
```
▶️ Try it live: munshi-bh9x34cncubzjqvgtzzuy.streamlit.app

Drop in a late bill and only the affected workers react. Every step traced in @neatlogs.
```
Check `@dodopayments` and `@crustdata` resolve to the official accounts in X's autocomplete before posting.

## Steps 2–3: form answers
- **Project name:** Munshi
- **Team:** Superposition (solo): Shivam Kumar
- **One-liner:** An AI CA that closes a messy month of books, recovers when they don't balance, and proves every number.
- **Problem:** Small businesses can't afford a CA every day. Month-end means owners sorting bank statements and
  receipt photos by hand; duplicate bills, vendor arithmetic errors, un-invoiced work and late payers slip through,
  and books that don't match the bank go unnoticed.
- **Solution:** Six AI workers close the month end to end: research real peers (SEC filings), read every bill
  (totals re-added in code; vendor errors flagged), match and categorise every bank line (Crustdata resolves
  cryptic payees), reconcile against the bank and hunt any gap until it's ₹0, draft invoices with Dodo payment links
  and reminders (owner approves), and brief the owner. New files (a late bill, a payment) are absorbed
  incrementally: only affected work is redone, and Munshi reports what changed.
- **How we used neatlogs:** every close is one traced session (business = end user). v1's failures (books ₹9,050 off,
  2/12 traps, wrong profit in the brief) were found in the traces and fixed in v2 (₹0, 12/12, −29% tokens).
- **How we used Entire:** Entire enabled on the repo with checkpoints; entire-graph used to navigate and analyse the
  code (outputs in `evidence/entire/`); the books themselves are versioned in Git, the same "why is this line here?"
  idea applied to accounting.
- **cfo.ai:** not used (the signup needed a payment card); Munshi's business plan is built from measured costs in
  `evidence/business-plan/`.
- **Other sponsors:** Dodo Payments (payment links on invoices Munshi drafts, test mode), Crustdata (company lookup
  for cryptic bank payees), neatHack LiteLLM models (Nova, Claude).
- **Repo:** https://github.com/shivamKumarG11/munshi
- **Live app:** https://munshi-bh9x34cncubzjqvgtzzuy.streamlit.app
- **Demo video:** [VIDEO LINK]
- **Evidence:** `evidence/results.md`; neatlogs sessions `close-studio-kaveri-2026-09-v1-023643` (v1) and
  `close-studio-kaveri-2026-09-v2-023726` (v2).
