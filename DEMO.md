# Final demo video script (≤ 3:00): sponsors all the way

Every segment names the sponsor doing the work, with its logo on screen. Covers the organisers' brief: the problem ·
how cfo.ai and Entire are part of the project · how neatlogs found and resolved Munshi's incidents.

Live app (public): https://munshi-bh9x34cncubzjqvgxtzzuy.streamlit.app

## Have open before recording
1. The app on **1 · Your month** (Studio Kaveri). Use the live link or run it locally.
2. **neatlogs** → your project → **Incidents** (per the organisers' how-to video) + one close trace + **Analytics** (cost).
3. Terminal in the repo: `entire status` and
   `entire graph search --query "where does munshi repair gaps between the ledger and the bank" --format text --top-k 3`
4. GitHub: `evidence/business-plan/business_plan.md`.

---

**[0:00–0:15] THE PROBLEM** · *Your month: category tiles → "View large" on the PrintWorks bill*
> "Small businesses can't afford a CA every day. Month-end is a bank statement and a pile of bills. Duplicates,
> vendor mistakes, un-billed work and late payers slip through, and the books stop matching the bank."

**[0:15–0:30] MEET THE TEAM** · *Hand it to the team → the office line; point at each logo badge*
> "Munshi is an AI CA: six workers, each powered by a sponsor. The models come from neatHack's Nova and Claude.
> Crustdata identifies who you paid. Dodo Payments gets you paid. And neatlogs traces every single step."

**[0:30–1:00] THE CLOSE, LIVE** · *workers light up; Meena's Crustdata badge; Dev: "off by ₹9,050" → "₹0"*
> "Arjun reads every bill on Nova and Claude, re-adding the totals in code, and he catches a vendor whose bill doesn't
> add up. Meena hits a cryptic 'RZP-Notion' payment; **Crustdata** resolves it to Notion, a software company, so it's
> booked as Software. Dev reconciles against the bank: off by ₹9,050. A duplicate bill and that vendor error. Fixed,
> re-checked: zero."

**[1:00–1:15] DODO PAYMENTS** · *Needs your OK → Approve "Invoice Zenith" → Pay link → the Dodo checkout page*
> "Sana found 40 hours nobody invoiced. One approval and **Dodo Payments** creates a real payment link, so the client
> can pay right now. Nothing goes out without the owner's OK."

**[1:15–1:55] NEATLOGS: INCIDENTS FOUND AND RESOLVED** · *neatlogs → Incidents → open each → its trace*
> "Every close is one **neatlogs** session, and its incidents showed us exactly where Munshi broke.
> One: version one closed the books ₹9,050 off and told the owner the wrong profit. The trace showed bills posted with
> no bank check, so we added reconciliation and a gap hunt.
> Two: the model provider went down, a 503 mid-close. neatlogs pinpointed the failing call, so Munshi now retries and
> switches provider automatically.
> Three: on real scanned receipts the reader crashed on dates like 15/01/2019. Fixed, and vendor accuracy went
> from 52 to 70 percent.
> And neatlogs' cost data told us a close costs about ₹1.39 in model calls."

**[1:55–2:15] ENTIRE** · *terminal: `entire status` → graph search result*
> "**Entire** is enabled on the repo with checkpoints, and our coding agent used entire-graph to find what to fix:
> ask where Munshi repairs gaps against the bank, and it lands straight on the gap-hunt function. The books
> themselves are versioned in Git too: Entire's 'why is this line here?', applied to accounting."

**[2:15–2:35] CFO.AI: OUTLINED** · *business_plan.md (unit economics + scenarios)*
> "A CA keeps the books correct; a CFO plans with them. That's where **cfo.ai** fits. Munshi exports each closed
> month's actuals for cfo.ai to plan from, and we modelled Munshi's own business for it: neatlogs-measured cost of
> ₹1.39 per close, Dodo billing, about 93% gross margin, break-even in month 13. The live connection is next; the
> signup needed a card."

**[2:35–2:52] THE PROOF** · *3 · Books & proof: tiles (neatlogs + Entire logos) → tap the Notion row*
> "Same month, before and after: ₹9,050 off becomes zero, 2 of 12 traps becomes 12 of 12, with 29% fewer tokens.
> Every entry shows the reason, and the worker and sponsor tool that decided it."

**[2:52–3:00] CLOSE** · *office, all ✓, logos visible*
> "Munshi, built with neatlogs, Entire, Dodo Payments and Crustdata. Your books. Closed. Proven."

---
Say once, anywhere natural: *"The demo business is generated; the reader is tested on real receipts."*

**2:20 cut for X:** keep Problem, Team, the Close, neatlogs (incidents one and two), Entire, and Proof; cut cfo.ai to
one line ("modelled for cfo.ai from neatlogs-measured costs") and drop the Dodo checkout page view.
