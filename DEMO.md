# Final demo video script (≤ 3:00)

Covers the organisers' brief: **the problem · how cfo.ai and Entire are part of the project · how neatlogs found
and resolved the incidents Munshi ran into.**

Live app (public): https://munshi-bh9x34cncubzjqvgxtzzuy.streamlit.app

## Have open before recording
1. The live app on **1 · Your month** (Studio Kaveri).
2. **neatlogs** → your project → **Incidents** (per the organisers' how-to video): the 503 model outage, the
   "temperature is deprecated" errors, and v1 session `close-studio-kaveri-2026-09-v1-023643`.
3. A terminal in the repo: `entire status` and
   `entire graph search --query "where does munshi repair gaps between the ledger and the bank" --format text --top-k 3`
4. `evidence/business-plan/business_plan.md` on GitHub.

---

**[0:00–0:20] THE PROBLEM** · *Your month: the category tiles, then "View large" on the PrintWorks bill*
> "Small businesses can't afford a CA every day. At month-end the owner has a bank statement and a pile of bills and
> receipt photos. Duplicate bills, vendor mistakes, work nobody invoiced and clients who pay late all slip through,
> and the books quietly stop matching the bank."

**[0:20–1:05] THE SOLUTION** · *"Hand it to the team →", the office lights up, Dev goes "off by ₹9,050" → "₹0", then Approve the Zenith invoice → Dodo pay link*
> "Munshi is an AI CA: six workers close the month. Riya researches real peers in SEC filings. Arjun reads every
> bill and re-adds the totals in code. Meena categorises every payment, and Crustdata identifies cryptic payees. Dev
> reconciles against the bank and won't stop until it's zero. Here it was off by ₹9,050: a bill uploaded twice
> and a vendor's wrong total. Found, fixed, re-checked. Sana drafts an invoice for un-billed work with a Dodo payment
> link, and nothing goes out without the owner's OK."

**[1:05–1:55] NEATLOGS: INCIDENTS FOUND AND RESOLVED** · *neatlogs → Incidents → open each one → its trace*
> "neatlogs traced every run, and its incidents showed us exactly where the agent broke.
> One: our first version closed the books ₹9,050 off and told the owner the wrong profit. The trace showed bills
> posted with no bank check, so we added reconciliation and a gap hunt.
> Two: the model provider went down, a 503, and a close stopped mid-run. The trace pinpointed the failing call, so
> Munshi now retries and switches provider automatically.
> Three: on real scanned receipts the reader crashed on dates like 15/01/2019. Fixed, and vendor accuracy went from
> 52 to 70 percent. Every fix was verified with a fresh trace."

**[1:55–2:20] ENTIRE** · *terminal: `entire status`, then the graph search result*
> "Entire is enabled on the repo, and our coding agent used entire-graph to find what to change. Asking where Munshi
> repairs gaps against the bank lands straight on the gap-hunt function. And the books themselves are versioned
> in Git: Entire's 'why is this line here?', applied to accounting."

**[2:20–2:35] CFO.AI: OUTLINED** · *business_plan.md (unit economics + scenarios)*
> "We outlined where cfo.ai fits: a CA keeps the books correct, a CFO plans with them. Munshi exports each closed
> month's actuals for cfo.ai to plan from, and we modelled Munshi's own business for it: pricing, about ₹1.39 of
> model cost per close measured in neatlogs, roughly 93% gross margin, break-even in month 13. Connecting it live is
> next; the signup needed a card."

**[2:35–2:52] THE RESULT** · *3 · Books & proof: proof tiles, tap the Notion row*
> "Same month, before and after: ₹9,050 off becomes zero, 2 of 12 traps becomes 12 of 12, with 29% fewer tokens.
> And every entry shows the reason and the worker who decided it."

**[2:52–3:00] CLOSE** · *back to the office, all ✓*
> "Munshi. Your books. Closed. Proven. Try it live: the link is in the post."

---
Say once, anywhere natural: *"The demo business is generated; the reader is tested on real receipts."*

**2:20 cut for X (if needed):** drop the cfo.ai segment to one sentence ("We modelled Munshi's business for cfo.ai
from costs neatlogs measured") and trim the solution to 0:20–0:55.
