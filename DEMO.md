# Demo video script (≤ 3:00): organisers' brief

The organisers asked for ONE video covering: **(1) the problem**, **(2) how cfo.ai and Entire were part of the
project**, **(3) how neatlogs was used to identify and resolve the incidents your agent ran into** (their
"critical incidents" feature; watch their how-to video linked in Discord before recording).

## Prepare (10 min)
- App: http://localhost:8501 (Studio Kaveri selected, fresh).
- **neatlogs dashboard** (app.neatlogs.com → your project): open **Incidents** (and Detections / Traces). Find the
  incidents for: the **503 "no available channel"** model outage, the **"temperature is deprecated"** errors, and
  the v1 close session `close-studio-kaveri-2026-09-v1-023643` (books off by ₹9,050). If Incidents is empty, follow
  the organisers' how-to video to file one from the failing traces.
- A terminal in the repo for Entire: `entire status` and
  `entire graph search --query "where does munshi repair gaps between the ledger and the bank" --format text --top-k 3`.
- `evidence/results.md` open in the browser (GitHub) for the before/after table.

## Script
| Time | Screen | Say |
| --- | --- | --- |
| **0:00–0:20** | **1 · Your month**: category tiles, then **View large** on the PrintWorks bill | **Problem.** "Small businesses can't afford a CA every day. At month-end, the owner is left with a bank statement and a pile of bills and receipt photos. Duplicate bills, vendor mistakes, work nobody invoiced and clients who pay late slip through, and the books quietly stop matching the bank." |
| **0:20–1:05** | **Hand it to the team →** · **2 · The office**: workers light up; Dev's bubble goes "off by ₹9,050" → "₹0"; approve the Zenith invoice → Dodo pay link | **Solution.** "Munshi is an AI CA: six workers close the month. Riya researches real peers in SEC filings, Arjun reads every bill and re-adds the totals in code, Meena categorises every payment, and Crustdata identifies cryptic payees. Dev reconciles against the bank, and he won't stop until it's zero. Here it was off by ₹9,050: a bill uploaded twice and a vendor's wrong total. Found, fixed, re-checked. Then Sana drafts an invoice with a Dodo payment link, and nothing goes out without the owner's OK." |
| **1:05–1:55** | **neatlogs → Incidents**: open each incident → its trace | **neatlogs: incidents found and resolved.** "neatlogs traced every run, and its incidents showed us where the agent broke. *One:* our first version closed the books ₹9,050 off and told the owner the wrong profit; the trace showed bills were posted with no bank check, so we added reconciliation and a gap hunt. *Two:* today the model provider went down, a 503, and a close stopped mid-run; the trace pinpointed the failing call, so Munshi now retries and switches provider automatically. *Three:* on real scanned receipts the reader crashed on dates like 15/01/2019; fixed, and vendor accuracy went from 52% to 70%. Every fix was verified with a new trace." |
| **1:55–2:20** | Terminal: `entire status` + the `entire graph search` result | **Entire.** "Entire is enabled on the repo, and our coding agent used entire-graph to find the code to change. Asking 'where does Munshi repair gaps against the bank' lands straight on the gap-hunt function. And the books themselves are versioned in Git: the same 'why is this line here?' idea, applied to accounting." |
| **2:20–2:35** | `evidence/business-plan/business_plan.md` | **cfo.ai (honest).** "We couldn't get cfo.ai access, because the signup needed a card. So we built Munshi's business plan from costs neatlogs measured: about ₹1.39 of model cost per close, roughly 93% gross margin." |
| **2:35–2:52** | **3 · Books & proof**: proof tiles; tap the Notion row | **Result.** "Same month, before and after: ₹9,050 off becomes zero, 2 of 12 traps becomes 12 of 12, 29% fewer tokens. And every entry shows the reason and the worker who decided it." |
| **2:52–3:00** | Back to the office, all ✓ | "Munshi. Your books. Closed. Proven." |

Say once: *"The demo business is generated; the reader is tested on real receipts."*

**X limit:** free accounts can attach up to 2:20. Either attach a 2:20 cut (drop the cfo.ai line and shorten the
solution segment) and put the full video on YouTube in your reply, or attach the full one if your account allows it.
